# Cloudinary Profile Picture Upload - Setup Guide

## What Was Added

Profile picture upload functionality using Cloudinary cloud storage service.

## New Features

1. **Profile Picture Upload to Cloudinary**
   - Users can upload profile pictures from the profile page
   - Images are automatically uploaded to Cloudinary
   - Images are automatically optimized (max 500x500px, JPG format)
   - Secure URLs are stored in the database

2. **Profile Management Page**
   - View and edit user profile information
   - Upload/change profile picture
   - Client-side image preview before upload
   - File size validation (max 5MB)
   - Image type validation

## Cloudinary Configuration

**Your Cloudinary credentials (configured in `backend/utils.py`):**
- Cloud Name: 
- API Key:
- API Secret: 

## Installation Steps

### 1. Install Cloudinary Package

From the `backend` directory:

```powershell
pip install cloudinary==1.36.0
```

Or install all requirements:

```powershell
pip install -r requirements.txt
```

### 2. Run the Application

```powershell
python app.py
```

### 3. Access Profile Page

After logging in, navigate to:
- `http://127.0.0.1:5000/profile`

Or click "My Profile" button on the home page.

## New Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/profile` | GET | View user profile |
| `/profile/update` | POST | Update profile with optional picture upload |

## How It Works

### Upload Process

1. User selects an image file on the profile page
2. Client-side JavaScript shows a preview
3. On form submit, the image is sent to the Flask server
4. `upload_image_to_cloudinary()` function uploads to Cloudinary with:
   - Folder: `user_profiles`
   - Public ID: `user_{user_id}`
   - Auto-resize: max 500x500px
   - Format: JPG
   - Quality: Auto-optimized
5. Cloudinary returns a secure URL
6. The URL is saved to `user.profile_pic_url` in MongoDB
7. The image is displayed on the profile page

### Image Optimization

Images are automatically:
- Resized to max 500x500px (maintains aspect ratio)
- Converted to JPG format
- Quality-optimized for web
- Stored securely on Cloudinary CDN

### Old Image Handling

When a user uploads a new profile picture:
- The `public_id` parameter with `overwrite=True` ensures the old image is replaced
- No duplicate images are created
- Storage space is efficiently managed

## Code Structure

### Modified Files

1. **`backend/requirements.txt`**
   - Added: `cloudinary==1.36.0`

2. **`backend/utils.py`**
   - Added Cloudinary configuration
   - Added `upload_image_to_cloudinary()` function
   - Added `delete_image_from_cloudinary()` function (for future use)

3. **`backend/controllers/user_controller.py`**
   - Enhanced `update_profile()` to handle file uploads
   - Added Cloudinary integration
   - Returns tuple `(user, error)` for better error handling

4. **`backend/views/home.py`**
   - Added `/profile` route (GET)
   - Added `/profile/update` route (POST)
   - Added file upload handling with `enctype="multipart/form-data"`

5. **`frontend/profile.html`** (NEW)
   - Profile view and edit page
   - File upload input with preview
   - Client-side validation (file size, type)
   - Bootstrap 5 styled UI

6. **`frontend/Home/home.html`**
   - Added "My Profile" button for logged-in users

## Testing

### Test Profile Upload

1. Login with existing user:
   - Email: `kaif@gmail.com`
   - Password: (your registration password)

2. Click "My Profile" button

3. Upload a profile picture:
   - Click "Choose File" under Profile Picture
   - Select an image (JPG, PNG, etc.)
   - Preview will appear
   - Click "Update Profile"

4. Verify:
   - Success message appears
   - Profile picture displays on the page
   - Image URL in MongoDB starts with `https://res.cloudinary.com/`

### Check Cloudinary Dashboard

1. Login to Cloudinary at: https://cloudinary.com/console
2. Navigate to Media Library
3. Look for folder: `user_profiles`
4. Find your uploaded images: `user_{user_id}`

## Security Notes

- File type validation (images only)
- File size limit (5MB client-side)
- Cloudinary handles malicious file detection
- Only logged-in users can upload
- Each user can only update their own profile
- Secure HTTPS URLs from Cloudinary

## Future Enhancements

- [ ] Move Cloudinary credentials to `.env` file
- [ ] Add image cropping tool
- [ ] Support multiple profile pictures/gallery
- [ ] Add profile picture deletion option
- [ ] Implement profile picture moderation
- [ ] Add image filters/effects

## Troubleshooting

### Import Error: "cloudinary could not be resolved"

**Solution:** Install the package:
```powershell
pip install cloudinary==1.36.0
```

### Upload Failed Error

**Possible causes:**
1. Check internet connection (Cloudinary is cloud-based)
2. Verify Cloudinary credentials are correct
3. Check file size (must be < 5MB)
4. Ensure file is a valid image format

### Profile Picture Not Showing

**Check:**
1. MongoDB `users` collection has `profile_pic_url` field populated
2. URL starts with `https://res.cloudinary.com/`
3. Browser can access Cloudinary URLs (check firewall/proxy)
4. Image was uploaded successfully (check Cloudinary dashboard)

## API Reference

### upload_image_to_cloudinary(file, folder, public_id)

**Parameters:**
- `file`: FileStorage object from `request.files`
- `folder`: Cloudinary folder name (default: "uploads")
- `public_id`: Custom ID for the image (optional)

**Returns:**
Dictionary with:
- `secure_url`: HTTPS URL of the uploaded image
- `public_id`: Cloudinary public ID
- `url`: HTTP URL
- `format`: Image format (jpg, png, etc.)
- `width`: Image width in pixels
- `height`: Image height in pixels

**Returns `None` on failure**

---

**Last Updated:** November 19, 2025
