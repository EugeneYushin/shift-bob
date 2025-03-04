import json
import logging
import os
from datetime import date, datetime
from functools import reduce
from logging import Logger
from operator import concat
from typing import Any, Callable, assert_never
from zoneinfo import ZoneInfo

from lenses import lens
from slack_bolt import Ack, App, BoltResponse, Respond, Say
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.models.blocks import (
    ActionsBlock,
    DatePickerElement,
    InputBlock,
    MarkdownTextObject,
    Option,
    PlainTextObject,
    SectionBlock,
    StaticSelectElement,
    TimePickerElement,
    UserMultiSelectElement,
)
from slack_sdk.models.views import View

from config import Config, SlackMode
from models import Rotation, Schedule, Temporal
from service.oncall import OncallService
from store.factory import StoreFactory

logging.basicConfig(level=logging.INFO)

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

store_factory = StoreFactory.apply(Config())


def match_ls(command: dict[str, Any]) -> bool:
    # available args
    # https://github.com/slackapi/bolt-python/blob/1a863715fdace5e59ef4e11b1ad606194e8a1c38/slack_bolt/kwargs_injection/utils.py#L21
    return str(command.get("text", "")) == "ls"


def match_create(command: dict[str, Any]) -> bool:
    return str(command.get("text", "")) == "create"


@app.middleware  # or app.use(log_request)
def log_request(
    logger: Logger, body: dict[str, Any], next: Callable[[], BoltResponse]
) -> BoltResponse:
    logger.debug(body)
    return next()


@app.command("/oncall", matchers=[match_ls])
def handle_list(
    body: dict[str, Any], ack: Ack, respond: Respond, client: WebClient, logger: Logger
) -> None:
    logger.info(body)
    ack()

    oncall_svc = OncallService(store_factory)
    shifts = oncall_svc.get_shifts(limit=5)
    logger.info(f"{shifts=}")

    if not shifts:
        respond(text=":poop: No shifts are set!", response_type="in_channel")
        return

    current_shift = shifts[0]
    firefighter = current_shift.firefighter

    # headers = [MarkdownTextObject(text="*Shifts:*"), MarkdownTextObject(text="*Swaps:*")]
    fields = [
        MarkdownTextObject(
            text=f"`{s.start_date.strftime('%a, %Y-%m-%d %H:%M')}` <@{s.firefighter}>"
        )
        for s in shifts
    ]
    # TODO pad with swaps
    padding_fields = [MarkdownTextObject(text=" ") for _ in shifts]
    tz = current_shift.start_date.tzname()

    respond(
        blocks=[
            SectionBlock(
                block_id="list_current",
                text=MarkdownTextObject(
                    text=f"*Current firefighter:* <@{firefighter}>"
                ),
            ),
            SectionBlock(
                block_id="list_shifts_header",
                fields=[
                    MarkdownTextObject(text="*Shifts:*"),
                    MarkdownTextObject(text="*Swaps:*"),
                ],
            ),
            SectionBlock(
                block_id="list_shifts",
                # slack_sdk.errors.SlackObjectFormationError: fields attribute cannot exceed 10 items
                fields=reduce(
                    concat,  # type: ignore[arg-type]
                    zip(fields, padding_fields),
                ),  # flatten pairwise (shifts+swaps side-by-side)
            ),
            SectionBlock(
                block_id="list_tz",
                # TODO format timezone (read it from rotation object)?!
                text=f"Timezone: {tz}",
            ),
        ],
        response_type="in_channel",
    )


@app.command("/oncall", matchers=[match_create])
def handle_create(
    body: dict[str, Any], ack: Ack, client: WebClient, logger: Logger
) -> None:
    logger.info(body)
    ack()

    client.views_open(
        trigger_id=body["trigger_id"],
        view=View(
            type="modal",
            callback_id="view-oncall-create",
            title=PlainTextObject(text="Create rotation"),
            submit=PlainTextObject(text="Submit"),
            close=PlainTextObject(text="Cancel"),
            blocks=[
                InputBlock(
                    block_id="fighters_block",
                    element=UserMultiSelectElement(
                        action_id="fighters_select",
                        placeholder=PlainTextObject(text="Choose you fighters"),
                        initial_users=[],
                    ),
                    label=PlainTextObject(text="Fighters"),
                ),
                ActionsBlock(
                    block_id="schedule_block",
                    elements=[
                        StaticSelectElement(
                            action_id="schedule_each_select",
                            options=[
                                Option(text=PlainTextObject(text=str(i)), value=str(i))
                                for i in range(1, 32)
                            ],
                            initial_option=Option(
                                text=PlainTextObject(text="1"), value="1"
                            ),
                        ),
                        StaticSelectElement(
                            action_id="schedule_temporal_select",
                            options=[
                                Option(text=PlainTextObject(text="days"), value="day"),
                                Option(
                                    text=PlainTextObject(text="weeks"), value="week"
                                ),
                            ],
                            initial_option=Option(
                                text=PlainTextObject(text="days"), value="day"
                            ),
                        ),
                    ],
                ),
                ActionsBlock(
                    block_id="start_end_block",
                    # use DatePickerElement + TimePickerElement over DateTimePickerElement for better UI alignment
                    elements=[
                        DatePickerElement(
                            action_id="start_date_select",
                            initial_date=date.today().isoformat(),
                        ),
                        TimePickerElement(
                            action_id="start_time_select",
                            initial_time="09:00",
                            timezone=Config().timezone,
                        ),
                    ],
                ),
            ],
        ),
    )


@app.view("view-oncall-create")
def view_submission(ack: Ack, body: dict[str, Any], logger: Logger) -> None:
    ack()
    logger.info(f"{json.dumps(body)=}")
    values_focus = lens.Get("view").Get("state").Get("values")

    option_val = lens.Get("selected_option").Get("value")
    each_focus = (
        values_focus
        & lens.Get("schedule_block").Get("schedule_each_select")
        & option_val
    )
    temporal_focus = (
        values_focus
        & lens.Get("schedule_block").Get("schedule_temporal_select")
        & option_val
    )

    each = body & each_focus.F(int).get()
    temporal = body & temporal_focus.F(Temporal).get()

    users = (
        body
        & (
            values_focus & lens["fighters_block"]["fighters_select"]["selected_users"]
        ).get()
    )

    start_date = (
        body
        & (
            values_focus & lens["start_end_block"]["start_date_select"]["selected_date"]
        ).get()
    )
    start_time_focus = lens["start_end_block"]["start_time_select"]
    start_time = body & (values_focus & start_time_focus & lens["selected_time"]).get()
    # TODO set default TZ from config if not passed
    start_time_tz = body & (values_focus & start_time_focus & lens["timezone"]).get()

    rotation = Rotation(
        schedule=Schedule(each=each, temporal=temporal),
        fighters=users,
        # TODO if start/end dates are timezone-aware, timezone field looks redundant
        start_date=datetime.fromisoformat(f"{start_date}T{start_time}").replace(
            tzinfo=ZoneInfo(start_time_tz)
        ),
        timezone=start_time_tz,
    )

    oncall_svc = OncallService(store_factory)
    shifts = oncall_svc.create_rotation(rotation)

    logger.info(f"{shifts[:5]=}")

    ack(":white_check_mark: Done!", response_type="ephemeral")  # in_channel


@app.event("app_mention")
def ping_firefighter(body: dict[str, Any], say: Say, logger: Logger) -> None:
    oncall_svc = OncallService(store_factory)
    shift = oncall_svc.get_current_shift()
    logger.info(f"current {shift=}")
    # TODO hint the future rotation/shifts if any
    if shift is None:
        say(":poop: No shifts are set!", thread_ts=body["event"]["ts"])
        return

    firefighter = shift.firefighter
    say(f"cc <@{firefighter}> as current firefighter", thread_ts=body["event"]["ts"])


if __name__ == "__main__":
    # Create an app-level token with connections:write scope
    cfg = Config()
    match cfg.mode:
        case SlackMode.http:
            app.start(port=int(os.environ.get("PORT", cfg.port)))
        case SlackMode.socket:
            handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
            handler.start()  # type:ignore[no-untyped-call]
        case default:
            assert_never(default)
