import json
import os
import sys
import shutil
import time
from jinja2.exceptions import TemplateSyntaxError
from jinja2 import Environment, FileSystemLoader, select_autoescape
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

env = Environment(
    loader=FileSystemLoader("./src"), autoescape=select_autoescape(["html", "xml"])
)


def generate(filename, context):
    template = env.get_template(filename)
    return template.render(**context)


def write(filename, output):
    open(os.path.join("output", filename), "w", encoding="utf8").write(output)


def grab_peaks():
    data = json.load(open(os.path.join("peaks.json"), "r"))
    data.sort(key=lambda x: x["name"].replace("Mt. ", ""))
    return data


def grab_strava():
    data = json.load(open(os.path.join("strava.json"), "r"))
    by_peak = {}
    for activity in data["activities"]:
        for peak in activity["peaks"]:
            assert peak not in by_peak
            by_peak[peak] = activity["strava"]
    return by_peak


def get_count(context):
    return {"total": len(context["peaks"]), "done": len(context["by_peak"])}


context = {"peaks": grab_peaks(), "by_peak": grab_strava()}

context.update(get_count(context))


def regenerate(event=None):
    try:
        for filename in os.listdir("src"):
            output = generate(filename, context)
            write(filename, output)
    except TemplateSyntaxError as error:
        print(error.__traceback__)

    shutil.copyfile(
        os.path.expanduser("~/c/vancouver-bagger/output/index.html"),
        os.path.expanduser("~/c/blog/files/peaks-bagged.html"),
    )


if __name__ == "__main__":
    if "--watch" in sys.argv:
        handler = FileSystemEventHandler()
        handler.dispatch = regenerate

        observer = Observer()
        observer.schedule(handler, "src", recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    else:
        regenerate()
