from micro.store import GraphModule

DISCORD_HTTP_RATE_LIMITS = GraphModule(
  id="micro.discord.http.rate_limits",
  schema="""
    type DiscordHTTPRoute @entity(key: ["id"]) {
      id: ID!
      bucketId: ID
    }

    type DiscordHTTPBucket @entity(key: ["id"]) {
      id: ID!
      limit: Int!
      remaining: Int!
      resetAt: Float!
      probeUntil: Float!
    }

    type DiscordHTTPGlobalLimit @entity(key: ["id"]) {
      id: ID!
      blockedUntil: Float!
    }

    type Query {
      discordHTTPRoute(id: ID!): DiscordHTTPRoute @from(key: {id: id})
      discordHTTPBucket(id: ID!): DiscordHTTPBucket @from(key: {id: id})
      discordHTTPGlobalLimit(id: ID!): DiscordHTTPGlobalLimit @from(key: {id: id})
    }

    type Mutation {
      createDiscordHTTPRoute(id: ID!, bucketId: ID): DiscordHTTPRoute!
        @insert(key: {id: id}, set: {id: id, bucketId: bucketId})
      mapDiscordHTTPRoute(id: ID!, bucketId: ID): DiscordHTTPRoute
        @update(key: {id: id}, set: {bucketId: bucketId})

      createDiscordHTTPBucket(id: ID!, limit: Int!, remaining: Int!, resetAt: Float!, probeUntil: Float!): DiscordHTTPBucket!
        @insert(
          key: {id: id}
          set: {id: id, limit: limit, remaining: remaining, resetAt: resetAt, probeUntil: probeUntil}
        )
      advanceDiscordHTTPBucket(id: ID!, limit: Int!, remaining: Int!, resetAt: Float!): DiscordHTTPBucket
        @update(
          key: {id: id}
          where: "current.resetAt < $resetAt"
          set: {limit: limit, remaining: remaining, resetAt: resetAt}
        )
      reduceDiscordHTTPBucket(id: ID!, remaining: Int!, resetAt: Float!): DiscordHTTPBucket
        @update(
          key: {id: id}
          where: "current.resetAt >= $resetAt AND current.remaining > $remaining"
          set: {remaining: remaining}
        )
      acquireDiscordHTTPBucket(id: ID!, now: Float!): DiscordHTTPBucket
        @update(
          key: {id: id}
          where: "current.remaining > 0 AND current.resetAt > $now"
          set: {remaining: "current.remaining - 1"}
        )
      claimExpiredDiscordHTTPBucket(id: ID!, now: Float!, leaseUntil: Float!): DiscordHTTPBucket
        @update(
          key: {id: id}
          where: "current.resetAt <= $now AND current.probeUntil <= $now"
          set: {remaining: "0", probeUntil: leaseUntil}
        )

      createDiscordHTTPGlobalLimit(id: ID!, blockedUntil: Float!): DiscordHTTPGlobalLimit!
        @insert(key: {id: id}, set: {id: id, blockedUntil: blockedUntil})
      extendDiscordHTTPGlobalLimit(id: ID!, until: Float!): DiscordHTTPGlobalLimit
        @update(
          key: {id: id}
          where: "current.blockedUntil < $until"
          set: {blockedUntil: until}
        )
    }
  """,
)

__all__ = ("DISCORD_HTTP_RATE_LIMITS",)
