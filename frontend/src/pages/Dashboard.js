import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, TrendingUp, MessageSquare } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const [stats, setStats] = useState({
    total_analyses: 0,
    sentiment_distribution: { positive: 0, negative: 0, neutral: 0 },
    by_type: { single: 0, bulk: 0, csv: 0, url: 0 }
  });
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, historyRes] = await Promise.all([
        axios.get(`${API}/stats`),
        axios.get(`${API}/history?limit=10`)
      ]);

      if (statsRes?.data) setStats(statsRes.data);
      if (historyRes?.data?.history) setHistory(historyRes.data.history);

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="spinner"></div>
      </div>
    );
  }

  const sentimentData = [
    { name: 'Positive', value: stats.sentiment_distribution.positive || 0, color: '#10B981' },
    { name: 'Negative', value: stats.sentiment_distribution.negative || 0, color: '#F43F5E' }
  ];

  const typeData = [
    { name: 'Single', value: stats.by_type.single || 0 },
    { name: 'Bulk', value: stats.by_type.bulk || 0 },
    { name: 'CSV', value: stats.by_type.csv || 0 },
    { name: 'URL', value: stats.by_type.url || 0 }
  ];

  return (
    <div className="px-6 lg:px-12 py-12">
      <div
        className="relative overflow-hidden rounded-2xl bg-white border border-[#E2E8F0] p-8 lg:p-12 mb-8"
        style={{
          backgroundImage: 'url(https://images.unsplash.com/photo-1765046255479-669cf07a0230?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDF8MHwxfHNlYXJjaHwxfHxhYnN0cmFjdCUyMGRhdGElMjB2aXN1YWxpemF0aW9uJTIwZ2VvbWV0cmljfGVufDB8fHx8MTc2ODc2NDk5N3ww&ixlib=rb-4.1.0&q=85)',
          backgroundSize: 'cover',
          backgroundPosition: 'center'
        }}
      >
        <div className="relative z-10 backdrop-blur-sm bg-white/90 rounded-xl p-8">
          <h1 className="text-4xl lg:text-5xl font-bold text-[#0A0A0A] mb-4" data-testid="dashboard-title">
            Sentiment Analysis Dashboard
          </h1>
          <p className="text-lg text-[#64748B] max-w-2xl">
            Analyze social media posts and product reviews with advanced AI-powered sentiment detection.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatsCard
          title="Total Analyses"
          value={stats.total_analyses || 0}
          icon={Activity}
          color="#002FA7"
          testId="total-analyses-card"
        />
        <StatsCard
          title="Positive Sentiment"
          value={stats.sentiment_distribution.positive || 0}
          icon={TrendingUp}
          color="#10B981"
          testId="positive-sentiment-card"
        />
        <StatsCard
          title="Recent Analyses"
          value={history.filter(h => h && h.sentiment !== 'neutral').length}
          icon={MessageSquare}
          color="#002FA7"
          testId="recent-analyses-card"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card className="border-[#E2E8F0]" data-testid="sentiment-distribution-card">
          <CardHeader>
            <CardTitle>Sentiment Distribution</CardTitle>
            <CardDescription>Positive vs Negative</CardDescription>
          </CardHeader>
          <CardContent>
            {sentimentData.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={sentimentData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `${entry.name}: ${entry.value}`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {sentimentData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-[#64748B]">
                No data available. Start analyzing to see results.
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-[#E2E8F0]" data-testid="analysis-type-card">
          <CardHeader>
            <CardTitle>Analysis Types</CardTitle>
            <CardDescription>Distribution by analysis method</CardDescription>
          </CardHeader>
          <CardContent>
            {typeData.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={typeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis dataKey="name" stroke="#64748B" />
                  <YAxis stroke="#64748B" />
                  <Tooltip />
                  <Bar dataKey="value" fill="#002FA7" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-[#64748B]">
                No data available. Start analyzing to see results.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="border-[#E2E8F0]" data-testid="recent-history-card">
        <CardHeader>
          <CardTitle>Recent Analyses</CardTitle>
          <CardDescription>Latest sentiment analysis results</CardDescription>
        </CardHeader>
        <CardContent>
          {history && history.filter(h => h && h.sentiment !== 'neutral').length > 0 ? (
            <div className="space-y-4">
              {history
                .filter(h => h && h.sentiment !== 'neutral')
                .map((item, index) => (
                  <div
                    key={item.id || index}
                    className="p-4 rounded-lg border border-[#E2E8F0] hover:shadow-md transition-shadow"
                    data-testid={`history-item-${index}`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <p className="text-sm text-[#0A0A0A] flex-1 mr-4">
                        {item.text || "No text content"}
                      </p>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap sentiment-${item.sentiment || 'neutral'}`}>
                        {(item.sentiment || 'UNKNOWN').toUpperCase()}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-[#64748B]">
                      <span>Confidence: {item.confidence ? (item.confidence * 100).toFixed(1) : '0.0'}%</span>
                      <span>Model: {item.model_used || 'Unknown'}</span>
                      <span>{item.timestamp ? new Date(item.timestamp).toLocaleString() : 'Just now'}</span>
                    </div>
                  </div>
                ))}
            </div>
          ) : (
            <div className="text-center py-12 text-[#64748B]">
              <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No analyses yet. Start by analyzing some text!</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

function StatsCard({ title, value, icon: Icon, color, testId }) {
  return (
    <Card className="border-[#E2E8F0] card-hover" data-testid={testId}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-[#64748B] mb-1">{title}</p>
            <p className="text-3xl font-bold text-[#0A0A0A]">{value}</p>
          </div>
          <div
            className="w-12 h-12 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: `${color}15` }}
          >
            <Icon className="w-6 h-6" style={{ color }} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default Dashboard;