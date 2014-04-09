Snapshot
========

Snapshot is a small Python script that takes a snapshot using a Foscam IP camera at a certain interval. The Foscam Python API was provided by [foscam-with-python project](https://code.google.com/p/foscam-with-python/). Snapshot only uses a subset of the functionality this library provides.

Snapshot puts the snapshots it collects into the following file structure: `YEAR/MONTH/DAY/snapshot-YEAR-MONTH-DAY_HOUR:MIN:SECOND.jpg`. It will automatically create this folder structure from where ever you run the script.

To run Snapshot,

```bash
./snapshot -l URL_TO_CAMERA -u USER_NAME -p PASSWORD -i INTERVAL_IN_SECONDS
```

For example, 
```bash
./snapshot -l 192.168.0.5:8213 -u phil -p foobar -i 3600
```

For more details, type `./snapshot -h`.
