Discord
=======

All Discord access goes through NATS, so no service holds a connection or the bot token and
any of them can be restarted, scaled or replaced independently.

.. code-block:: text

   Discord ⇄ GatewayWorker ──► events ──► your services, InteractionRouter, GatewayProjection
   Discord ⇄ InteractionEndpoint (HTTP alternative to the Gateway) ──► InteractionRouter
   your services ──► DiscordHTTPClient ──► DiscordHTTPWorker ⇄ Discord (REST)

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - I want to...
     - Read
   * - receive events (messages, members, reactions)
     - :doc:`events`, running on a :doc:`gateway`
   * - handle slash commands, buttons and modals
     - :doc:`interactions`
   * - call any Discord API operation, or send a message
     - :doc:`api`, :doc:`ui`, run by the :doc:`http-worker`
   * - look up members, roles and channels without a REST call
     - :doc:`state`
   * - add commands while the bot runs
     - :doc:`runtime-commands`
   * - run without a Gateway connection
     - :doc:`endpoint`
   * - change or block outgoing requests, or measure them
     - :doc:`http-worker`

Configuration
-------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Variable
     - Meaning
   * - ``DISCORD_TOKEN``
     - The bot token. Set it in ``.env`` or the environment; it is read by workers and never
       stored in NATS. Rotate it by rolling the processes.
   * - ``DISCORD_API_URL``
     - Point workers at another API with Discord's shape, such as a proxy or a fake for
       testing (or pass ``api_url=`` to the workers).
   * - ``DISCORD_PUBLIC_KEY``
     - The application's public key, for :doc:`endpoint`.
   * - ``DISCORD_APPLICATION_ID``
     - For ``micro invite`` when it cannot be read from the token.

Invite links
------------

``micro invite`` prints the link that adds the bot to a server and the one that installs its
commands on a user's account. It reads the application ID from ``DISCORD_TOKEN`` (or
``DISCORD_APPLICATION_ID``) and the permissions from micro.toml:

.. code-block:: toml

   [invite]
   permissions = ["view_channel", "send_messages", "embed_links"]   # names or numbers

.. code-block:: console

   micro invite                    # both links
   micro invite -p admin           # other permissions, once
   micro invite --guild 1234       # preselect (and lock) one server

Names are Discord's (``manage_roles``, ``Moderate Members``, ...); a typo is caught with a
suggestion, and also when ``micro dev`` loads micro.toml. Enable *User Install* under
Installation in the Developer Portal for the second link to work. In code:

.. code-block:: python

   from micro.discord.invite import Permissions, invite_url

   invite_url("1234", permissions=Permissions.SEND_MESSAGES | Permissions.EMBED_LINKS)
   invite_url("1234", install="user")      # also: guild_id=, redirect_uri=, state=

.. api::
   micro.discord.invite.Permissions
   micro.discord.invite.invite_url
   micro.discord.invite.parse_permissions
   micro.discord.invite.application_id
   micro.discord.invite.AUTHORIZE_URL
