from micro.store import GraphModule

GATEWAY_PROJECTION = GraphModule(
  id="micro.gateway.projection",
  schema="""
    scalar JSON

    type GatewayConnection @entity(key: ["id"]) {
      id: ID!
      shardId: Int!
      active: Boolean!
      state: String!
      data: [DiscordObject!]!
    }

    type DiscordObject @entity(key: ["connectionId", "kind", "id"]) {
      connectionId: ID!
      kind: String!
      id: ID!
      guildId: ID
      payload: JSON!
    }

    type Query {
      gatewayConnection(id: ID!): GatewayConnection @from(key: {id: id})
      discordObject(connectionId: ID!, kind: String!, id: ID!): DiscordObject
        @fromActive(
          key: {connectionId: connectionId, kind: kind, id: id}
          ownerType: "GatewayConnection"
          ownerKey: {id: connectionId}
          ownerField: "data"
          activeField: "active"
        )
      projectionDiscordObject(connectionId: ID!, kind: String!, id: ID!): DiscordObject
        @from(key: {connectionId: connectionId, kind: kind, id: id})
      projectionDiscordObjects(first: Int!, offset: Int!): [DiscordObject!]! @scan
    }

    type Mutation {
      createGatewayConnection(id: ID!, shardId: Int!, active: Boolean!, state: String!): GatewayConnection!
        @insert(key: {id: id}, set: {id: id, shardId: shardId, active: active, state: state})
      updateGatewayConnection(id: ID!, active: Boolean!, state: String!): GatewayConnection
        @update(key: {id: id}, set: {active: active, state: state})
      deleteGatewayConnection(id: ID!): Boolean!
        @delete(type: "GatewayConnection", key: {id: id})
      createDiscordObject(connectionId: ID!, kind: String!, id: ID!, guildId: ID, payload: JSON!): DiscordObject!
        @insert(
          key: {connectionId: connectionId, kind: kind, id: id}
          set: {connectionId: connectionId, kind: kind, id: id, guildId: guildId, payload: payload}
        )
      updateDiscordObject(connectionId: ID!, kind: String!, id: ID!, guildId: ID, payload: JSON!): DiscordObject
        @update(
          key: {connectionId: connectionId, kind: kind, id: id}
          set: {guildId: guildId, payload: payload}
        )
      deleteDiscordObject(connectionId: ID!, kind: String!, id: ID!): Boolean!
        @delete(type: "DiscordObject", key: {connectionId: connectionId, kind: kind, id: id})
      attachDiscordObject(connectionId: ID!, kind: String!, id: ID!): Boolean!
        @connect(
          fromType: "GatewayConnection"
          fromKey: {id: connectionId}
          toType: "DiscordObject"
          toKey: {connectionId: connectionId, kind: kind, id: id}
          field: "data"
        )
    }
  """,
)

__all__ = ("GATEWAY_PROJECTION",)
