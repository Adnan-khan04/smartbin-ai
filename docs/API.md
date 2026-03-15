# API Documentation - SmartBin AI

## Base URL
```
http://localhost:8000/api
```

## Authentication

### Register User
**POST** `/auth/register`

Request:
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "username": "ecouser"
}
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### Login User
**POST** `/auth/login`

Request:
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### Logout
**POST** `/auth/logout`

Response:
```json
{
  "message": "Logged out successfully"
}
```

## Classification

### Classify Waste from Image
**POST** `/classify/image`

Request: `multipart/form-data`
- `file`: Image file (JPG, PNG, etc.)

Response:
```json
{
  "waste_type": "plastic",
  "confidence": 0.95,
  "disposal_location": "Recycle Bin (Yellow Container)",
  "description": "Plastic waste - can be recycled into new products"
}
```

### Get Waste Categories
**GET** `/classify/categories`

Response:
```json
{
  "plastic": "Bottles, bags, containers, packaging",
  "paper": "Newspapers, magazines, cardboard, books",
  "metal": "Cans, foil, wires, utensils",
  "organic": "Food waste, leaves, grass, compost"
}
```

## Gamification

### Add Points to User
**POST** `/gamification/add-points/{user_id}/{points}`

Response:
```json
{
  "message": "Added 10 points",
  "user_id": "user123"
}
```

### Get User Stats
**GET** `/gamification/user-stats/{user_id}`

Response:
```json
{
  "user_id": "user123",
  "points": 250,
  "rank": "Apprentice",
  "badges": [
    {
      "id": "first_class",
      "name": "First Step",
      "description": "Classify your first item",
      "icon": "🎯"
    }
  ],
  "level": 2
}
```

### Get Leaderboard
**GET** `/gamification/leaderboard?limit=10`

Response:
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "user": "eco_warrior_1",
      "points": 5000
    },
    {
      "rank": 2,
      "user": "green_guardian",
      "points": 4500
    }
  ]
}
```

### Get All Badges
**GET** `/gamification/badges`

Response:
```json
[
  {
    "id": "first_class",
    "name": "First Step",
    "description": "Classify your first item",
    "icon": "🎯"
  },
  {
    "id": "ten_class",
    "name": "Active Recycler",
    "description": "Classify 10 items",
    "icon": "♻️"
  }
]
```

### Get All Ranks
**GET** `/gamification/ranks`

Response:
```json
{
  "ranks": [
    "Novice",
    "Apprentice",
    "Expert",
    "Master",
    "Legendary"
  ]
}
```

## Dashboard

### Get User Impact
**GET** `/dashboard/impact/{user_id}`

Response:
```json
{
  "total_items_recycled": 42,
  "co2_saved": 15.5,
  "plastic_recycled": 8.2,
  "paper_recycled": 5.1,
  "metal_recycled": 1.8,
  "organic_waste": 2.4,
  "last_updated": "2024-01-17T10:30:00"
}
```

### Get Global Impact
**GET** `/dashboard/global-impact`

Response:
```json
{
  "total_items_recycled": 15000,
  "total_co2_saved": 5000.0,
  "active_users": 250,
  "total_plastic_recycled": 3000.0,
  "total_paper_recycled": 2500.0,
  "total_metal_recycled": 1200.0,
  "last_updated": "2024-01-17T10:30:00"
}
```

### Get Classification History
**GET** `/dashboard/history/{user_id}?limit=20`

Response:
```json
{
  "user_id": "user123",
  "history": [
    {
      "id": 1,
      "waste_type": "plastic",
      "points_earned": 15,
      "timestamp": "2024-01-17T10:30:00"
    }
  ]
}
```

## Users

### Get User Profile
**GET** `/users/{user_id}`

Response:
```json
{
  "user_id": "user123",
  "username": "eco_user",
  "email": "user@example.com",
  "avatar": null,
  "bio": "I love saving the planet!",
  "joined_date": "2024-01-01"
}
```

## User Profile

### Update User Profile
**PUT** `/users/{user_id}`

Request:
```json
{
  "username": "new_username",
  "bio": "New bio",
  "avatar": "https://example.com/avatar.jpg"
}
```

Response:
```json
{
  "message": "Profile updated successfully"
}
```

### Delete User Account
**DELETE** `/users/{user_id}`

Response:
```json
{
  "message": "User deleted successfully"
}
```

## Error Responses

### Bad Request
```json
{
  "detail": "Invalid input"
}
```

### Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### Not Found
```json
{
  "detail": "Resource not found"
}
```

### Server Error
```json
{
  "detail": "Internal server error"
}
```

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 500 | Server Error |

## Rate Limiting

Currently no rate limiting. Add in production!

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

## Testing API

### Using Swagger UI
Visit: `http://localhost:8000/docs`

### Using ReDoc
Visit: `http://localhost:8000/redoc`

### Using cURL

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"pass","username":"testuser"}'

# Classify Image
curl -X POST http://localhost:8000/api/classify/image \
  -F "file=@image.jpg"

# Get Stats
curl http://localhost:8000/api/gamification/user-stats/user123
```

---

**API Version**: 1.0.0  
**Last Updated**: 2024-01-17
