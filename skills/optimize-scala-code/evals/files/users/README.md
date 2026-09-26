# users service

Request handlers call `UserService.loadAll` and then `UserService.score`.
The production database pool has 16 connections, so no more than 16
`Dao.load` calls may run at once. Hosts have 8 cores.
