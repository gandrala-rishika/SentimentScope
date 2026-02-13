import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import '@/App.css';
import Dashboard from '@/pages/Dashboard';
import SocialMediaAnalysis from '@/pages/SocialMediaAnalysis';
import ProductReviewAnalysis from '@/pages/ProductReviewAnalysis';
import { BarChart3, Twitter, ShoppingCart, Info } from 'lucide-react';
import { Toaster } from '@/components/ui/sonner';

function App() {
  const [activeNav, setActiveNav] = useState('dashboard');

  return (
    <BrowserRouter>
      <div className="App min-h-screen bg-[#F8F9FA]">
        <Toaster position="top-right" />

        <header className="sticky top-0 z-50 backdrop-blur-xl bg-white/80 border-b border-black/5">
          <div className="px-6 lg:px-12 py-4 flex items-center justify-between">
            <Link to="/" onClick={() => setActiveNav('dashboard')} className="flex items-center gap-3">
              <div className="w-10 h-10 bg-[#002FA7] rounded-lg flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-[#0A0A0A] tracking-tight" style={{ fontFamily: 'Manrope, sans-serif' }}>
                SentimentScope
              </h1>
            </Link>

            <nav className="hidden md:flex items-center gap-2">
              <NavLink
                to="/"
                icon={BarChart3}
                label="Dashboard"
                active={activeNav === 'dashboard'}
                onClick={() => setActiveNav('dashboard')}
              />
              <NavLink
                to="/social-media"
                icon={Twitter}
                label="Social Media"
                active={activeNav === 'social'}
                onClick={() => setActiveNav('social')}
              />
              <NavLink
                to="/product-reviews"
                icon={ShoppingCart}
                label="Product Reviews"
                active={activeNav === 'product'}
                onClick={() => setActiveNav('product')}
              />
            </nav>
          </div>
        </header>

        <main className="">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/social-media" element={<SocialMediaAnalysis />} />
            <Route path="/product-reviews" element={<ProductReviewAnalysis />} />
          </Routes>
        </main>

        <footer className="mt-20 border-t border-[#E2E8F0] bg-white">
          <div className="px-6 lg:px-12 py-8 text-center text-sm text-[#64748B]">
            <p>&copy; 2025 SentimentScope. Built with DistilBERT for advanced sentiment analysis.</p>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}

function NavLink({ to, icon: Icon, label, active, onClick }) {
  return (
    <Link
      to={to}
      onClick={onClick}
      data-testid={`nav-${label.toLowerCase().replace(' ', '-')}`}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-200 ${active
          ? 'bg-[#002FA7] text-white'
          : 'text-[#64748B] hover:bg-[#F8F9FA] hover:text-[#0A0A0A]'
        }`}
    >
      <Icon className="w-4 h-4" />
      <span className="font-medium text-sm">{label}</span>
    </Link>
  );
}

export default App;