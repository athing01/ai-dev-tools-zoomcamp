# e-Business Card Generator

## Goal

Create a simple web application that allows a user to create a digital business card from their personal and contact information.

The application should generate the completed business card as a PNG image, including a QR code that points to a URL provided by the user.

## User

A person who wants to create a digital business card for sharing their contact information.

## Product Specification

### Language

The user can select the primary language of the business card:

- Thai
- English

The primary language determines the main language used on the card.

### Name

The user can provide:

- Name in the primary language — required
- Name in the other language — optional

### Role

The user can provide:

- Thai role — optional
- English role — optional

The role does not have to exist in both languages.

For example, a user may select Thai as the primary language but provide only an English role.

### Photo

The user can:

- Include a photo
- Not use a photo

The photo is optional.

### Company

The user can optionally provide:

- Company name in Thai
- Company name in English

The company information is optional to support freelancers and people who do not represent a company.

### Contact Address

The user can optionally provide a contact address.

### Phone

The user can provide a phone number.

### Email

The user can provide an email address.

### Social Links

The user can optionally provide additional social links.

### QR Destination

The user can provide a URL.

The generated QR code should point to this URL.

The application does not need to create or host the destination page.

## Card Layout

The user can choose between:

- Portrait
- Landscape

The user can also choose whether the card uses a photo.

The MVP therefore supports four layout combinations:

1. Portrait with photo
2. Portrait without photo
3. Landscape with photo
4. Landscape without photo

## Output

After entering the information and selecting the layout, the user can generate a business card as a PNG image.

The generated PNG should contain:

- The supplied business-card information
- The selected layout
- The photo when selected and provided
- The QR code generated from the supplied URL

## MVP Features

The specification settles on four main features:

1. **Card Information** — enter and validate business-card information.
2. **QR Code** — generate a QR code from a user-provided URL.
3. **Card Layout** — choose portrait/landscape and whether to use a photo.
4. **PNG Generation** — generate and download the completed business card as a PNG.

## Out of Scope

The MVP does not include:

- JPG output
- HTML profile pages
- Profile hosting
- Automatic profile URLs
- Database-backed card storage
- User accounts or authentication
- Persistent card management
- Drag-and-drop card editing
- Custom template designer
- Custom fonts or advanced visual customization
- Social network API integrations

These may be considered in a later version.
