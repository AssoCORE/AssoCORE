class Date:
    day: int
    month: int
    year: int
    hour: int
    minute: int

class Notification:
    date: Date
    message: str
    from_id: int
    read: bool

class Reminder:
    date: Date
    title: str
    description: str

class User:
    notifications: list[Notification]
    reminders: list[Reminder]
    roles: list[int]
    name: str
    firstname: str
    username: str
    password: str
    mail: str
    phone: str
    age: int
    id: int

class Event:
    registered_users: list[int]
    staff: list[int]
    creator: User
    start_date: Date
    end_date: Date
    title: str
    description: str
    registrations_limits: int
