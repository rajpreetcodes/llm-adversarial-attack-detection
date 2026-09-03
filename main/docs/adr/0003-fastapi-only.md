# ADR 0003: FastAPI-only backend (no Node/Express gateway)

## Status
Accepted (recorded for mentor sign-off; the synopsis mentioned both).

## Context
The synopsis listed FastAPI and a Node/Express gateway. Two backends double
the deployment surface, the auth surface, and the testing burden for a
three-person team, while the entire detection engine is Python.

## Decision
One backend: FastAPI serves the detection API, the OpenAI-compatible proxy,
and the admin routes. Node exists only for the dashboard build (Vite), which
produces static assets.

## Consequences
- One language for all server code; one test stack; one Dockerfile for the API.
- The OpenAI-compatible schema means client SDKs work unchanged, which
  preserves the integration story the gateway was for.
- If a hard requirement for a Node gateway appears later, it can be added as a
  thin proxy in front of this API without changing it.

## Alternatives considered
- FastAPI + Express as per the synopsis: rejected as redundant.
- Express-only: rejected; the detection engine is Python/ML.
