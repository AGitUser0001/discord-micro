from micro.store import GraphModule

GATEWAY_PROJECTION = GraphModule(
  id="micro.gateway.state",
  schema="""
    scalar JSON

    # A connection of a shard. It only remembers which guilds it delivered, so that
    # losing it can mark them as not current.
    type GatewayConnection @entity(key: ["id"]) {
      id: ID!
      shardId: Int!
      guilds: [GatewayGuild!]!
    }

    # One guild's state, whichever shard and connection delivered it. `fresh` is false
    # while the connection that delivered it has a gap; `synced` once a full GUILD_CREATE
    # was applied (so a list of its channels or roles is complete, not just what events
    # happened to carry).
    type GatewayGuild @entity(key: ["id"]) {
      id: ID!
      connectionId: ID!
      fresh: Boolean!
      synced: Boolean!
      data: [DiscordObject!]!
      channels: [DiscordObject!]!
      roles: [DiscordObject!]!
    }

    type DiscordObject @entity(key: ["guildId", "kind", "id"]) {
      guildId: ID!
      kind: String!
      id: ID!
      payload: JSON!
    }

    # Where an object with a globally unique id (a channel, a role) lives.
    type DiscordIndex @entity(key: ["kind", "id"]) {
      kind: String!
      id: ID!
      guildId: ID!
    }

    type Query {
      gatewayConnection(id: ID!): GatewayConnection @from(key: {id: id})
      gatewayGuild(id: ID!): GatewayGuild @from(key: {id: id})
      discordObject(guildId: ID!, kind: String!, id: ID!): DiscordObject
        @from(key: {guildId: guildId, kind: kind, id: id})
      discordIndex(kind: String!, id: ID!): DiscordIndex @from(key: {kind: kind, id: id})
    }

    type Mutation {
      createGatewayConnection(id: ID!, shardId: Int!): GatewayConnection!
        @insert(key: {id: id}, set: {id: id, shardId: shardId})
      deleteGatewayConnection(id: ID!): Boolean!
        @delete(type: "GatewayConnection", key: {id: id})
      attachGuildToConnection(connectionId: ID!, guildId: ID!): Boolean!
        @connect(
          fromType: "GatewayConnection"
          fromKey: {id: connectionId}
          toType: "GatewayGuild"
          toKey: {id: guildId}
          field: "guilds"
        )

      createGatewayGuild(id: ID!, connectionId: ID!, fresh: Boolean!, synced: Boolean!): GatewayGuild!
        @insert(
          key: {id: id}
          set: {id: id, connectionId: connectionId, fresh: fresh, synced: synced}
        )
      updateGatewayGuild(id: ID!, connectionId: ID!, fresh: Boolean!, synced: Boolean!): GatewayGuild
        @update(key: {id: id}, set: {connectionId: connectionId, fresh: fresh, synced: synced})
      deleteGatewayGuild(id: ID!): Boolean!
        @delete(type: "GatewayGuild", key: {id: id})

      createDiscordObject(guildId: ID!, kind: String!, id: ID!, payload: JSON!): DiscordObject!
        @insert(
          key: {guildId: guildId, kind: kind, id: id}
          set: {guildId: guildId, kind: kind, id: id, payload: payload}
        )
      updateDiscordObject(guildId: ID!, kind: String!, id: ID!, payload: JSON!): DiscordObject
        @update(key: {guildId: guildId, kind: kind, id: id}, set: {payload: payload})
      deleteDiscordObject(guildId: ID!, kind: String!, id: ID!): Boolean!
        @delete(type: "DiscordObject", key: {guildId: guildId, kind: kind, id: id})
      attachDiscordObject(guildId: ID!, kind: String!, id: ID!): Boolean!
        @connect(
          fromType: "GatewayGuild"
          fromKey: {id: guildId}
          toType: "DiscordObject"
          toKey: {guildId: guildId, kind: kind, id: id}
          field: "data"
        )
      attachChannel(guildId: ID!, kind: String!, id: ID!): Boolean!
        @connect(
          fromType: "GatewayGuild"
          fromKey: {id: guildId}
          toType: "DiscordObject"
          toKey: {guildId: guildId, kind: kind, id: id}
          field: "channels"
        )
      attachRole(guildId: ID!, kind: String!, id: ID!): Boolean!
        @connect(
          fromType: "GatewayGuild"
          fromKey: {id: guildId}
          toType: "DiscordObject"
          toKey: {guildId: guildId, kind: kind, id: id}
          field: "roles"
        )

      createDiscordIndex(kind: String!, id: ID!, guildId: ID!): DiscordIndex!
        @insert(key: {kind: kind, id: id}, set: {kind: kind, id: id, guildId: guildId})
      deleteDiscordIndex(kind: String!, id: ID!): Boolean!
        @delete(type: "DiscordIndex", key: {kind: kind, id: id})
    }
  """,
)

__all__ = ("GATEWAY_PROJECTION",)
