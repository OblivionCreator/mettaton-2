# mettaton-2

PREREQUISITES:

discord.py 1.6.0 or higher - Runs the bot<br>
pyDrive - Runs automated backups every 24hr

FILES YOU NEED TO PROVIDE TO GET BOT TO FUNCTION:

token.txt - The Bot Token on Discord.<br>
client_secrets.json - For automatic backups to function, you will need to define a client_secrets.json from the Google Drive API<br>
.config - The bot will create this file. Use rp!setgmchannel to configure where the bot sends any GM based alerts.

The bot currently works off of 3 role names: - Please ensure these roles exist or the bot will not function correctly!

'Gamemaster' - A role that gives the user ability to modify any existing characters.

'Roleplayer' - A user is assigned this role upon any of their characters being approved.

'NPC' - The bot will ignore any users with this role.


This bot is free to use and licensed under AGPLv3

    Mettaton 2.0 RP Bot
    Copyright (C) 2020 - OblivionCreator

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
