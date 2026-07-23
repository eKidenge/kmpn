{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% load static %}

{% block title %}Set New Password - KPSN{% endblock %}

{% block extra_css %}
<style>
    .password-reset-wrapper {
        padding: 60px 0 80px;
        background: linear-gradient(135deg, #f5f0e8 0%, #e8e0d0 50%, #f0ece0 100%);
        min-height: 80vh;
        display: flex;
        align-items: center;
    }
    
    .password-reset-card {
        background: var(--white);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-lg);
        border: 1px solid rgba(201, 168, 76, 0.2);
        overflow: hidden;
        transition: var(--transition-normal);
    }
    
    .password-reset-card .card-header {
        background: linear-gradient(135deg, var(--dark-blue) 0%, var(--primary-color) 50%, var(--navy-blue) 100%);
        padding: 30px 35px 25px;
        border-bottom: 4px solid var(--gold-color);
        text-align: center;
    }
    
    .password-reset-card .card-header .reset-icon {
        font-size: 3rem;
        color: var(--gold-color);
        display: block;
        margin-bottom: 8px;
        opacity: 0.8;
    }
    
    .password-reset-card .card-header h3 {
        font-family: var(--font-heading);
        font-size: 1.8rem;
        font-weight: 900;
        color: var(--white);
        margin-bottom: 4px;
        letter-spacing: 1px;
    }
    
    .password-reset-card .card-header .gold-text {
        color: var(--gold-color);
    }
    
    .password-reset-card .card-header .decorative-line {
        width: 60px;
        height: 3px;
        background: var(--gold-color);
        margin: 10px auto 8px;
        border-radius: var(--radius-full);
    }
    
    .password-reset-card .card-body {
        padding: 35px 40px 40px;
    }
    
    .password-reset-card .form-group {
        margin-bottom: 20px;
    }
    
    .password-reset-card .form-label {
        font-family: var(--font-secondary);
        font-weight: 600;
        font-size: 0.85rem;
        color: var(--gray-800);
        margin-bottom: 5px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .password-reset-card .form-label .field-icon {
        color: var(--gold-color);
        font-size: 0.8rem;
        width: 16px;
    }
    
    .password-reset-card .form-label .required-star {
        color: var(--danger-color);
        margin-left: 2px;
        font-size: 1rem;
    }
    
    .password-reset-card .form-control {
        border: 2px solid #d4c8b0;
        border-radius: var(--radius-sm);
        padding: 10px 15px;
        font-family: var(--font-secondary);
        font-size: 0.95rem;
        transition: var(--transition-normal);
        background: var(--white);
        width: 100%;
        color: var(--gray-800);
        line-height: 1.5;
    }
    
    .password-reset-card .form-control:focus {
        border-color: var(--gold-color);
        box-shadow: 0 0 0 3px rgba(201, 168, 76, 0.12);
        outline: none;
    }
    
    .password-reset-card .btn-reset {
        background: linear-gradient(135deg, var(--gold-color) 0%, var(--gold-dark) 100%);
        color: var(--white);
        border: none;
        padding: 12px 30px;
        font-family: var(--font-heading);
        font-weight: 700;
        font-size: 1rem;
        border-radius: var(--radius-sm);
        transition: var(--transition-normal);
        cursor: pointer;
        text-transform: uppercase;
        letter-spacing: 1px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        width: 100%;
    }
    
    .password-reset-card .btn-reset:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(201, 168, 76, 0.3);
        color: var(--white);
    }
    
    @media (max-width: 768px) {
        .password-reset-wrapper {
            padding: 30px 0 50px;
        }
        
        .password-reset-card .card-header {
            padding: 20px;
        }
        
        .password-reset-card .card-header h3 {
            font-size: 1.4rem;
        }
        
        .password-reset-card .card-body {
            padding: 25px 20px 30px;
        }
    }
</style>
{% endblock %}

{% block content %}
<section class="password-reset-wrapper">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-lg-6 col-md-8">
                
                <div class="password-reset-card" data-aos="fade-up" data-aos-duration="800">
                    
                    <div class="card-header">
                        <i class="fas fa-lock reset-icon"></i>
                        <h3>
                            Set New <span class="gold-text">Password</span>
                        </h3>
                        <div class="decorative-line"></div>
                        <p class="reset-subtitle">
                            Enter your new password below
                        </p>
                    </div>
                    
                    <div class="card-body">
                        
                        {% if messages %}
                            {% for message in messages %}
                                <div class="alert alert-{% if message.tags == 'error' %}danger{% elif message.tags == 'success' %}success{% else %}info{% endif %}" role="alert">
                                    <i class="fas fa-{% if message.tags == 'error' %}exclamation-circle{% elif message.tags == 'success' %}check-circle{% else %}info-circle{% endif %}"></i>
                                    <span>{{ message }}</span>
                                </div>
                            {% endfor %}
                        {% endif %}
                        
                        <form method="post" novalidate>
                            {% csrf_token %}
                            
                            <div class="form-group">
                                <label for="{{ form.new_password1.id_for_label }}" class="form-label">
                                    <i class="fas fa-key field-icon"></i>
                                    New Password
                                    <span class="required-star">*</span>
                                </label>
                                <input type="password" name="{{ form.new_password1.name }}" 
                                       id="{{ form.new_password1.id_for_label }}" 
                                       class="form-control {% if form.new_password1.errors %}is-invalid{% endif %}"
                                       placeholder="Enter your new password"
                                       required>
                                <div class="form-text">
                                    <i class="fas fa-info-circle me-1"></i>
                                    Minimum 8 characters with letters and numbers
                                </div>
                                {% if form.new_password1.errors %}
                                    <div class="invalid-feedback">
                                        {{ form.new_password1.errors|join:", " }}
                                    </div>
                                {% endif %}
                            </div>
                            
                            <div class="form-group">
                                <label for="{{ form.new_password2.id_for_label }}" class="form-label">
                                    <i class="fas fa-check-circle field-icon"></i>
                                    Confirm New Password
                                    <span class="required-star">*</span>
                                </label>
                                <input type="password" name="{{ form.new_password2.name }}" 
                                       id="{{ form.new_password2.id_for_label }}" 
                                       class="form-control {% if form.new_password2.errors %}is-invalid{% endif %}"
                                       placeholder="Confirm your new password"
                                       required>
                                {% if form.new_password2.errors %}
                                    <div class="invalid-feedback">
                                        {{ form.new_password2.errors|join:", " }}
                                    </div>
                                {% endif %}
                            </div>
                            
                            <div class="d-grid gap-2 mt-3">
                                <button type="submit" class="btn-reset" id="resetBtn">
                                    <i class="fas fa-check me-2"></i> 
                                    Reset Password
                                </button>
                            </div>
                            
                        </form>
                        
                    </div>
                    
                </div>
                
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const form = document.querySelector('form');
        const resetBtn = document.getElementById('resetBtn');
        
        if (form && resetBtn) {
            form.addEventListener('submit', function() {
                resetBtn.disabled = true;
                resetBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Resetting...';
            });
        }
    });
</script>
{% endblock %}
