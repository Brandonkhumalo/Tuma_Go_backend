# 🚚 TumaGo Backend – Mobile Package Delivery Platform

TumaGo is a full-stack logistics platform that enables users to book local package deliveries and allows drivers to accept jobs based on their vehicle type (motorbike, van, or truck). This repository contains the **Django backend** powering real-time client-driver communication, delivery management, and asynchronous task handling.

---

## 🚀 Features

- 📦 **Client-Driver Matching** based on vehicle type and location
- 🔐 **JWT Authentication** with single sign-on and role-based access (User & Driver)
- 🌐 **Real-Time Communication** via Django Channels, WebSockets, and Daphne
- 📬 **Push Notifications** using Firebase Cloud Messaging
- ⚙️ **Asynchronous Tasks** with Dramatiq and Redis
- 🔁 **Delivery State Management** (Pending → Accepted → In-Transit → Delivered)
- 🗺️ **Google Maps Integration** handled by the mobile app
- 🐳 **Containerized Deployment** using Docker

---

## 🧠 Tech Stack

| Layer         | Tools Used                                                                 |
|---------------|------------------------------------------------------------------------------|
| **Backend**   | Django, Django REST Framework, Django Channels, Daphne                      |
| **Auth**      | JWT (JSON Web Tokens)                                                       |
| **Realtime**  | WebSockets, Channels, Daphne                                                |
| **Async Tasks**| Dramatiq, Redis                                                            |
| **Database**  | MySQL                                                                       |
| **Notifications** | Firebase Cloud Messaging                                                |
| **Containerization** | Docker                                                               |

---

## 🙋‍♂️ Author

**Brandon Khumalo**  
🚀 Backend & Mobile Developer  
📫 [LinkedIn](https://www.linkedin.com/in/brandon-khumalo04) | [Email](mailto:brandonkhumz40@gmail.com)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

**Live API URL**
[api demo](https://tumago.onrender.com/swagger/)