# Operational Metrics

## Purpose

This project includes a lightweight observability layer for tracking pipeline execution.

The goal is to make each pipeline run easier to inspect, debug, and validate.

## Metrics Captured

The current metrics layer records:

- Pipeline name
- Pipeline start time
- Pipeline end time
- Pipeline status
- Step name
- Step start time
- Step end time
- Step status
- Row count, when available
- Error message, when a step fails

## Current Implementation

Metrics are defined in:

```text
src/de_lakehouse_pipeline/metrics.py