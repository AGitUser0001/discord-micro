# Micro

Micro is an extensible library for building applications from independently replaceable microservices.

Its first major use case is a distributed Discord bot platform that Panel could later use.

Micro has three independent parts:

## `micro.overseer`

`micro.overseer` is the coordinator.

It oversees the complete deployment, including:

- coordinating microservice instances;
- assigning and transferring work;
- monitoring availability;
- handling service startup, shutdown, replacement, and recovery;
- coordinating Gateway workers and shard ownership;
- coordinating Gateway generations and rolling transitions.

It coordinates services without implementing their application logic.

## `micro.gateway`

`micro.gateway` is a Discord Gateway worker.

Each worker:

- maintains Discord WebSocket connections;
- operates the shards currently assigned to it;
- forwards raw Discord payloads to appropriate services;
- executes WebSocket operations through its owned connections;
- changes shard assignments as directed by the overseer;
- participates in recovery and rolling Gateway replacement.

A Gateway worker is not permanently tied to particular shard IDs. If one worker becomes unavailable, another can claim its shards. When it returns, it may be assigned different work.

Gateway generations allow a new collection of workers and connections to start before the old generation is retired. This supports rolling upgrades and shard-count changes.

Guild-scoped WebSocket operations can be routed to the worker owning the guild’s shard.

Global WebSocket control remains an open design problem. Its semantics should be determined later rather than prematurely generalized.

## `micro.service`

`micro.service` is the framework for writing a microservice.

It provides the common integration needed for a service to participate in a Micro deployment, along with reusable **microservice templates**.

A template is an abstraction implemented through functions, classes, decorators, context managers, or similar programming constructs. It packages a particular service-side behavior so individual services do not need to repeatedly implement its mechanics.

Templates may support behaviors involving:

- communication;
- lifecycle;
- work handling;
- concurrency;
- coordination;
- state;
- recovery;
- observability.

The available templates are not a fixed taxonomy. More can be added, and existing templates can be changed, combined, or replaced.

Applications can create any number and kind of microservices with `micro.service`. Discord HTTP handling and application features are examples of services rather than fixed parts of Micro.

## Extensibility

Micro does not prescribe a complete service topology.

- The overseer coordinates the deployment.
- Gateway workers operate Discord Gateway connections.
- The service framework supports arbitrary application microservices.
- Templates provide reusable behavior without restricting what a service can be.
- Applications and extensions can introduce new services and new templates.

Micro should avoid embedding assumptions from Panel or its first deployment into the general service framework.

Its architecture will be refined through implementation rather than completely specified in advance.

Reference:
 - other project: ~/Desktop/Panel
