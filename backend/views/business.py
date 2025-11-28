# views/business.py
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from controllers import business_controller
from werkzeug.utils import secure_filename

business_bp = Blueprint('business', __name__, url_prefix='/business')


@business_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_business():
    """Create a new business"""
    if request.method == 'GET':
        return render_template('business/create.html')
    
    try:
        # Get form data
        data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'street_house': request.form.get('street_house'),
            'city': request.form.get('city'),
            'district': request.form.get('district'),
            'description': request.form.get('description', ''),
            'category': request.form.get('category')
        }
        
        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'street_house', 'city', 'district', 'category']
        for field in required_fields:
            if not data.get(field):
                flash(f'{field.replace("_", " ").title()} is required', 'danger')
                return render_template('business/create.html'), 400
        
        # Get uploaded files
        profile_pic = request.files.get('profile_pic')
        gallery_pics = request.files.getlist('gallery_pics')
        
        # Create business
        business = business_controller.create_business(
            owner_id=current_user.user_id,
            data=data,
            profile_pic=profile_pic if profile_pic and profile_pic.filename else None,
            gallery_pics=[pic for pic in gallery_pics if pic and pic.filename]
        )
        
        flash(f'Business "{business.name}" created successfully!', 'success')
        return redirect(url_for('business.view_business', business_id=business.business_id))
        
    except Exception as e:
        flash(f'Error creating business: {str(e)}', 'danger')
        return render_template('business/create.html'), 500


@business_bp.route('/<business_id>')
def view_business(business_id):
    """View a single business with booking functionality"""
    business_details = business_controller.get_business_details(business_id)
    if not business_details:
        flash('Business not found', 'danger')
        return redirect(url_for('home.index'))
    
    # Get services for this business
    services = business_controller.get_services_by_business(business_id)
    
    # gallery_urls is already populated by get_business_details from controller
    # No need to parse or manipulate it here
    
    return render_template('business_detail.html', 
                         business=business_details, 
                         services=services)


@business_bp.route('/<business_id>/update', methods=['GET', 'POST'])
@login_required
def update_business(business_id):
    """Update business information"""
    business = business_controller.get_business(business_id)
    if not business:
        flash('Business not found', 'danger')
        return redirect(url_for('business.list_businesses'))
    
    # Check ownership
    if business.owner_id != current_user.user_id:
        flash('You are not authorized to edit this business', 'danger')
        return redirect(url_for('business.view_business', business_id=business_id))
    
    if request.method == 'GET':
        return render_template('business/update.html', business=business)
    
    try:
        # Get form data
        data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'street_house': request.form.get('street_house'),
            'city': request.form.get('city'),
            'district': request.form.get('district'),
            'description': request.form.get('description'),
            'category': request.form.get('category')
        }
        
        # Get uploaded files
        profile_pic = request.files.get('profile_pic')
        gallery_pics = request.files.getlist('gallery_pics')
        
        # Update business
        business_controller.update_business(
            business_id=business_id,
            data=data,
            profile_pic=profile_pic if profile_pic and profile_pic.filename else None,
            gallery_pics=[pic for pic in gallery_pics if pic and pic.filename]
        )
        
        flash('Business updated successfully!', 'success')
        return redirect(url_for('business.view_business', business_id=business_id))
        
    except Exception as e:
        flash(f'Error updating business: {str(e)}', 'danger')
        return render_template('business/update.html', business=business), 500


@business_bp.route('/list')
def list_businesses():
    """List businesses with optional filters"""
    category = request.args.get('category')
    city = request.args.get('city')
    district = request.args.get('district')
    
    businesses = business_controller.list_businesses(
        category=category,
        city=city,
        district=district
    )
    
    return render_template('business/list.html', businesses=businesses, 
                         category=category, city=city, district=district)


@business_bp.route('/<business_id>/deactivate', methods=['POST'])
@login_required
def deactivate_business(business_id):
    """Deactivate a business"""
    business = business_controller.get_business(business_id)
    if not business:
        flash('Business not found', 'danger')
        return redirect(url_for('business.list_businesses'))
    
    # Check ownership
    if business.owner_id != current_user.user_id:
        flash('You are not authorized to deactivate this business', 'danger')
        return redirect(url_for('business.view_business', business_id=business_id))
    
    try:
        business_controller.deactivate_business(business_id)
        flash('Business deactivated successfully', 'success')
        return redirect(url_for('home.dashboard'))
    except Exception as e:
        flash(f'Error deactivating business: {str(e)}', 'danger')
        return redirect(url_for('business.view_business', business_id=business_id))


@business_bp.route('/<business_id>/gallery/delete', methods=['POST'])
@login_required
def delete_gallery_image(business_id):
    """Delete an image from business gallery"""
    business = business_controller.get_business(business_id)
    if not business or business.owner_id != current_user.user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    gallery_url = request.json.get('gallery_url')
    if not gallery_url:
        return jsonify({'error': 'Gallery URL required'}), 400
    
    try:
        business_controller.delete_gallery_image(business_id, gallery_url)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Service Routes
@business_bp.route('/<business_id>/services')
def list_services(business_id):
    """List all services for a business"""
    business = business_controller.get_business(business_id)
    if not business:
        flash('Business not found', 'danger')
        return redirect(url_for('business.list_businesses'))
    
    services = business_controller.get_services_by_business(business_id)
    return render_template('business/services.html', business=business, services=services)


@business_bp.route('/<business_id>/services/create', methods=['GET', 'POST'])
@login_required
def create_service(business_id):
    """Create a new service for a business"""
    business = business_controller.get_business(business_id)
    if not business or business.owner_id != current_user.user_id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('business.list_businesses'))
    
    if request.method == 'GET':
        return render_template('business/create_service.html', business=business)
    
    try:
        data = {
            'name': request.form.get('name'),
            'description': request.form.get('description', ''),
            'price': float(request.form.get('price')),
            'duration_minutes': int(request.form.get('duration_minutes', 60))
        }
        
        service = business_controller.create_service(business_id, data)
        flash(f'Service "{service.name}" created successfully!', 'success')
        return redirect(url_for('business.list_services', business_id=business_id))
        
    except Exception as e:
        flash(f'Error creating service: {str(e)}', 'danger')
        return render_template('business/create_service.html', business=business), 500


@business_bp.route('/services/<service_id>/update', methods=['GET', 'POST'])
@login_required
def update_service(service_id):
    """Update a service"""
    service = business_controller.get_service(service_id)
    if not service:
        flash('Service not found', 'danger')
        return redirect(url_for('home.dashboard'))
    
    business = business_controller.get_business(service.business_id)
    if business.owner_id != current_user.user_id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('business.view_business', business_id=service.business_id))
    
    if request.method == 'GET':
        return render_template('business/update_service.html', service=service, business=business)
    
    try:
        data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'price': float(request.form.get('price')),
            'duration_minutes': int(request.form.get('duration_minutes'))
        }
        
        business_controller.update_service(service_id, data)
        flash('Service updated successfully!', 'success')
        return redirect(url_for('business.list_services', business_id=service.business_id))
        
    except Exception as e:
        flash(f'Error updating service: {str(e)}', 'danger')
        return render_template('business/update_service.html', service=service, business=business), 500