import React, { useState } from 'react';
import axios from 'axios';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Twitter, Send, Loader2, Video, Link2 } from 'lucide-react';
import { toast } from 'sonner';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SocialMediaAnalysis = () => {
  const [activeTab, setActiveTab] = useState('single');
  const [singleText, setSingleText] = useState('');
  const [bulkTexts, setBulkTexts] = useState('');
  const [videoUrl, setVideoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const analyzeSingleText = async () => {
    if (!singleText.trim()) {
      toast.error('Please enter some text to analyze');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/analyze/text`, { text: singleText });
      setResult({ type: 'single', data: response.data });
      toast.success('Analysis complete!');
    } catch (error) {
      console.error('Error analyzing text:', error);
      toast.error('Failed to analyze text. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const analyzeBulkTexts = async () => {
    const textArray = bulkTexts.split('\n').filter(t => t.trim());

    if (textArray.length === 0) {
      toast.error('Please enter texts (one per line)');
      return;
    }

    if (textArray.length > 100) {
      toast.error('Maximum 100 texts allowed');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/analyze/bulk`, { texts: textArray });
      setResult({ type: 'bulk', data: response.data });
      toast.success(`Analyzed ${textArray.length} texts successfully!`);
    } catch (error) {
      console.error('Error analyzing bulk texts:', error);
      toast.error('Failed to analyze texts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const analyzeVideoUrl = async () => {
    if (!videoUrl.trim()) {
      toast.error('Please enter a video URL');
      return;
    }

    setLoading(true);
    setResult(null);
    try {
      const response = await axios.post(`${API}/analyze/url`, { url: videoUrl });
      setResult({ type: 'url', data: response.data });
      toast.success('Video analysis complete!');
    } catch (error) {
      console.error('Error analyzing URL:', error);
      toast.error(error.response?.data?.detail || 'Failed to analyze URL. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="px-6 lg:px-12 py-12">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-[#1DA1F2]/10 rounded-lg flex items-center justify-center">
            <Twitter className="w-6 h-6 text-[#1DA1F2]" />
          </div>
          <div>
            <h1 className="text-3xl lg:text-4xl font-bold text-[#0A0A0A]" data-testid="social-media-title">
              Social Media Analysis
            </h1>
            <p className="text-[#64748B]">Analyze sentiment from posts and video comments</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <Card className="border-[#E2E8F0]" data-testid="input-card">
            <CardHeader>
              <CardTitle>Input Text</CardTitle>
              <CardDescription>Enter social media posts or video links</CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-3 mb-4">
                  <TabsTrigger value="single" data-testid="single-tab">Single Post</TabsTrigger>
                  <TabsTrigger value="bulk" data-testid="bulk-tab">Bulk Analysis</TabsTrigger>
                  <TabsTrigger value="video-link" data-testid="video-link-tab">Video Link</TabsTrigger>
                </TabsList>

                <TabsContent value="single" className="space-y-4">
                  <Textarea
                    placeholder="Enter a tweet, post, or comment..."
                    value={singleText}
                    onChange={(e) => setSingleText(e.target.value)}
                    rows={8}
                    className="resize-none"
                    data-testid="single-text-input"
                  />
                  <Button
                    onClick={analyzeSingleText}
                    disabled={loading}
                    className="w-full bg-[#002FA7] hover:bg-[#00227A]"
                    data-testid="analyze-single-btn"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4 mr-2" />
                        Analyze Sentiment
                      </>
                    )}
                  </Button>
                </TabsContent>

                <TabsContent value="bulk" className="space-y-4">
                  <Textarea
                    placeholder="Enter multiple posts, one per line..."
                    value={bulkTexts}
                    onChange={(e) => setBulkTexts(e.target.value)}
                    rows={8}
                    className="resize-none"
                    data-testid="bulk-text-input"
                  />
                  <Button
                    onClick={analyzeBulkTexts}
                    disabled={loading}
                    className="w-full bg-[#002FA7] hover:bg-[#00227A]"
                    data-testid="analyze-bulk-btn"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4 mr-2" />
                        Analyze All
                      </>
                    )}
                  </Button>
                </TabsContent>

                <TabsContent value="video-link" className="space-y-4">
                  <div className="space-y-4">
                    <div className="relative">
                      <Video className="absolute left-3 top-3 text-[#64748B] w-5 h-5" />
                      <input
                        type="url"
                        placeholder="Paste YouTube link..."
                        value={videoUrl}
                        onChange={(e) => setVideoUrl(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 rounded-md border border-[#E2E8F0] focus:outline-none focus:ring-2 focus:ring-[#002FA7]"
                        data-testid="video-url-input"
                      />
                    </div>
                    <div className="bg-[#F8F9FA] p-4 rounded-lg text-sm text-[#64748B]">
                      <p className="flex items-center gap-2 mb-1"><Link2 className="w-4 h-4" /> Supported Platforms:</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>YouTube (Videos, Shorts)</li>
                      </ul>
                    </div>
                    <Button
                      onClick={analyzeVideoUrl}
                      disabled={loading}
                      className="w-full bg-[#002FA7] hover:bg-[#00227A]"
                      data-testid="analyze-video-btn"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Fetching & Analyzing...
                        </>
                      ) : (
                        <>
                          <Video className="w-4 h-4 mr-2" />
                          Analyze Video
                        </>
                      )}
                    </Button>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>

        <div>
          {result ? (
            result.type === 'single' ? (
              <SingleResult data={result.data} />
            ) : (
              <BulkOrUrlResults data={result.data} type={result.type} />
            )
          ) : (
            <Card className="border-[#E2E8F0] h-full flex items-center justify-center">
              <CardContent className="text-center py-12">
                <Twitter className="w-16 h-16 mx-auto mb-4 text-[#64748B] opacity-50" />
                <p className="text-[#64748B]">Analysis results will appear here</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

function SingleResult({ data }) {
  const sentimentColors = {
    Positive: '#10B981',
    Negative: '#F43F5E',
    Neutral: '#94A3B8'
  };

  if (!data) {
    return <div className="text-center py-4 text-gray-500">No data available.</div>;
  }

  const scores = typeof data?.scores === 'object' && data?.scores !== null ? data.scores : {};
  const sentiment = data?.sentiment || 'Neutral';
  const confidence = data?.confidence || 0;

  return (
    <Card className="border-[#E2E8F0]" data-testid="single-result-card">
      <CardHeader>
        <CardTitle>Analysis Result</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="text-center p-6 bg-[#F8F9FA] rounded-lg">
          <Badge
            className={`text-lg px-6 py-2 sentiment-${sentiment.toLowerCase()}`}
            data-testid="sentiment-badge"
          >
            {sentiment}
          </Badge>
          <p className="text-sm text-[#64748B] mt-2">Confidence: {(confidence * 100).toFixed(1)}%</p>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-[#0A0A0A] mb-3">Sentiment Scores</h3>
          {Object.entries(scores)
            .filter(([s]) => s !== 'neutral')
            .map(([s, score]) => {
              const numericScore = Number(score) || 0;
              const scoreKey = s.charAt(0).toUpperCase() + s.slice(1);
              const barColor = sentimentColors[scoreKey] || '#ccc';
              return (
                <div key={s} className="mb-2">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="capitalize text-[#64748B]">{s}</span>
                    <span className="font-medium text-[#0A0A0A]">{(numericScore * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-[#F1F5F9] rounded-full overflow-hidden">
                    <div
                      className="h-full transition-all duration-500"
                      style={{
                        width: `${numericScore * 100}%`,
                        backgroundColor: barColor
                      }}
                    />
                  </div>
                </div>
              );
            })}
        </div>

        <div className="text-xs text-[#64748B] pt-4 border-t border-[#E2E8F0]">
          Model: {data?.model_used || 'Unknown'}
        </div>
      </CardContent>
    </Card>
  );
}

function BulkOrUrlResults({ data, type }) {
  const [showAllComments, setShowAllComments] = useState(false);
  const [commentSearch, setCommentSearch] = useState('');

  if (!data) return <div className="text-center py-4 text-gray-500">No data available.</div>;

  const summary = typeof data?.summary === 'object' && data?.summary !== null ? data.summary : {};
  const word_frequencies = typeof data?.word_frequencies === 'object' && data?.word_frequencies !== null ? data.word_frequencies : {};
  const ai_summary = data?.ai_summary;
  const metadata = typeof data?.metadata === 'object' && data?.metadata !== null ? data.metadata : {};
  const results = Array.isArray(data?.results) ? data.results : [];

  const sentiment_counts = summary?.sentiment_counts || { positive: 0, negative: 0 };
  const sentiment_percentages = summary?.sentiment_percentages || { positive: 0, negative: 0 };

  const pieData = [
    { name: 'Positive', value: Number(sentiment_counts.positive) || 0, color: '#10B981' },
    { name: 'Negative', value: Number(sentiment_counts.negative) || 0, color: '#F43F5E' }
  ];

  const wordChartData = Object.entries(word_frequencies)
    .map(([word, count]) => ({ word, count: Number(count) || 0 }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  const filteredComments = results.filter(item =>
    item.text.toLowerCase().includes(commentSearch.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {type === 'url' && metadata?.title && (
        <Card className="border-[#002FA7] bg-[#F0F4FF] shadow-md">
          <CardHeader>
            <CardTitle className="text-[#002FA7] text-xl">
              Analyzing: {metadata.title}
            </CardTitle>
            <CardDescription className="text-[#002FA7]">
              {metadata.description || "Video Content Analysis"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-[#0A0A0A] leading-relaxed whitespace-pre-line">
              {ai_summary || "AI Summary generation in progress..."}
            </p>
          </CardContent>
        </Card>
      )}

      <Card className="border-[#E2E8F0]" data-testid="bulk-summary-card">
        <CardHeader>
          <CardTitle>Summary</CardTitle>
          <CardDescription>Analyzed {summary?.total_analyzed || 0} {type === 'url' ? 'comments' : 'texts'}</CardDescription>
        </CardHeader>
        <CardContent>
          {Array.isArray(pieData) && pieData.some(d => d.value > 0) ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-gray-400">
              No sentiment data to display
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 mt-4">
            {Object.entries(sentiment_percentages)
              .filter(([sentiment]) => sentiment !== 'neutral')
              .map(([sentiment, percentage]) => (
                <div key={sentiment} className="text-center p-3 bg-[#F8F9FA] rounded-lg">
                  <p className="text-2xl font-bold text-[#0A0A0A]">{Number(percentage).toFixed(1)}%</p>
                  <p className="text-xs text-[#64748B] capitalize">{sentiment}</p>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>

      {Object.keys(word_frequencies).length > 0 && (
        <Card className="border-[#E2E8F0]">
          <CardHeader>
            <CardTitle>Top Words</CardTitle>
            <CardDescription>Most frequent words in analyzed text</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={wordChartData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
                <XAxis type="number" stroke="#64748B" />
                <YAxis dataKey="word" type="category" width={80} stroke="#64748B" tick={{ fontSize: 12 }} />
                <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                <Bar dataKey="count" fill="#002FA7" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {results.length > 0 ? (
        <Card className="border-[#E2E8F0]">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Analyzed Comments</CardTitle>
              {!showAllComments && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAllComments(true)}
                >
                  View All ({results.length})
                </Button>
              )}
            </div>
          </CardHeader>

          {showAllComments && (
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Search comments..."
                  value={commentSearch}
                  onChange={(e) => setCommentSearch(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAllComments(false)}
                >
                  Close
                </Button>
              </div>

              <div className="max-h-[500px] overflow-y-auto space-y-3 pr-2">
                {filteredComments.length > 0 ? (
                  filteredComments.map((item, index) => (
                    <div key={index} className="p-3 border border-[#E2E8F0] rounded-lg bg-white">
                      <p className="text-sm text-[#0A0A0A] leading-snug">{item.text}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-center text-sm text-gray-500 py-4">No comments match your search.</p>
                )}
              </div>
            </CardContent>
          )}
        </Card>
      ) : (
        <Card className="border-[#E2E8F0]">
          <CardHeader>
            <CardTitle>Analyzed Comments</CardTitle>
            <CardDescription>No comments found for this video.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8">
              <p className="text-[#64748B]">The comments section for this video might be disabled or empty.</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default SocialMediaAnalysis;