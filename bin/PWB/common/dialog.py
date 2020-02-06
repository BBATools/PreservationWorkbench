#! python3

# Copyright (C) 2020 Morten Eek

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from common.shell import pwb_cmd

def pwb_yes_no_prompt(message, height=100, width=500):
    question = pwb_cmd([
        'zenity', '--question', message, '--title=PWB',
        '--height={}'.format(height), '--width={}'.format(width),
        '--text={}'.format(message)
    ])
    return question.succeeded