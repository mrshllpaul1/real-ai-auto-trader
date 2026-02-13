import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  MessageCircle, Send, Loader2, Sparkles, GraduationCap,
  BookOpen, Brain, Lightbulb, RefreshCw, Trash2, ChevronDown,
  ChevronRight, HelpCircle, CheckCircle, XCircle, Trophy,
  Target, Clock, Zap, Search
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';
import ReactMarkdown from 'react-markdown';
import { PageLoadingSkeleton } from '../components/LoadingSkeleton';

const AITeacher = ({ embedded = false }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [topics, setTopics] = useState(null);
  const [glossary, setGlossary] = useState([]);
  const [glossarySearch, setGlossarySearch] = useState('');
  const [quiz, setQuiz] = useState(null);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [level, setLevel] = useState('intermediate');
  const [sessionId] = useState(() => `teach_${Date.now()}`);
  const [activeTab, setActiveTab] = useState('chat');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadTopics();
    loadGlossary();
    // Welcome message
    setMessages([{
      type: 'ai',
      content: `# 👨‍🏫 Welcome to AI Master Teacher!

I'm here to help you **deeply understand** crypto, trading, and blockchain technology.

For every topic, I'll explain:
- **WHO** - The people and history behind it
- **WHAT** - What it actually is and does
- **WHEN** - Timeline and when to use it
- **WHERE** - Where it exists and operates
- **WHY** - Why it matters and was created
- **HOW** - How it works, step by step

## 🎯 Try asking me:
- "What is Bitcoin and why does it matter?"
- "How do I read candlestick charts?"
- "Explain DeFi like I'm 5"
- "What is RSI and how do traders use it?"

**Select your experience level** above, and let's start learning! 📚`,
      timestamp: new Date().toISOString()
    }]);
  }, []);

  const loadTopics = async () => {
    try {
      const response = await api.get('/ai-teach/topics');
      setTopics(response.data);
    } catch (error) {
      console.error('Error loading topics:', error);
    }
  };

  const loadGlossary = async (search = '') => {
    try {
      const params = search ? { search } : {};
      const response = await api.get('/ai-teach/glossary', { params });
      setGlossary(response.data.terms || []);
    } catch (error) {
      console.error('Error loading glossary:', error);
    }
  };

  const loadQuiz = async (topic) => {
    try {
      const response = await api.get(`/ai-teach/quiz/${topic}`, { params: { difficulty: level } });
      setQuiz(response.data.quiz);
      setQuizAnswers({});
      setQuizSubmitted(false);
      setActiveTab('quiz');
    } catch (error) {
      console.error('Error loading quiz:', error);
      toast.error('Failed to load quiz');
    }
  };

  const sendMessage = useCallback(async (message) => {
    if (!message.trim()) return;

    const userMessage = {
      type: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      const response = await api.post('/ai-teach/ask', {
        query: message,
        session_id: sessionId,
        level: level,
        include_market_context: true
      }, { timeout: 90000 });

      const aiMessage = {
        type: 'ai',
        content: response.data.response,
        related_topics: response.data.related_topics,
        follow_up_questions: response.data.follow_up_questions,
        source: response.data.source,
        timestamp: response.data.timestamp
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        type: 'ai',
        content: "I apologize, but I encountered an error. Please try again or rephrase your question.",
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
      toast.error('Failed to get response');
    } finally {
      setLoading(false);
    }
  }, [sessionId, level]);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputValue);
    }
  };

  const handleQuickQuestion = (question) => {
    setInputValue(question);
    sendMessage(question);
  };

  const clearHistory = async () => {
    try {
      await api.delete(`/ai-teach/history/${sessionId}`);
      setMessages([{
        type: 'ai',
        content: "History cleared! What would you like to learn about?",
        timestamp: new Date().toISOString()
      }]);
      toast.success('Conversation cleared');
    } catch (error) {
      toast.error('Failed to clear history');
    }
  };

  const submitQuiz = () => {
    setQuizSubmitted(true);
    let correct = 0;
    quiz.questions.forEach((q, i) => {
      if (quizAnswers[i] === q.correct) correct++;
    });
    const percentage = Math.round((correct / quiz.questions.length) * 100);
    toast.success(`Quiz Complete! You scored ${correct}/${quiz.questions.length} (${percentage}%)`);
  };

  const renderMessage = (message, index) => {
    const isAI = message.type === 'ai';
    
    return (
      <motion.div
        key={index}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`flex ${isAI ? 'justify-start' : 'justify-end'} mb-4`}
      >
        <div className={`max-w-[85%] ${isAI ? 'bg-[#1A1A2E]' : 'bg-[#9D00FF]/20'} rounded-2xl p-4`}>
          {isAI && (
            <div className="flex items-center gap-2 mb-2">
              <GraduationCap size={18} className="text-[#9D00FF]" />
              <span className="text-sm font-medium text-[#9D00FF]">AI Teacher</span>
            </div>
          )}
          
          <div className={`${isAI ? 'prose prose-invert prose-sm max-w-none' : 'text-white'}`}>
            {isAI ? (
              <ReactMarkdown
                components={{
                  h1: ({node, ...props}) => <h1 className="text-xl font-bold text-white mb-3" {...props} />,
                  h2: ({node, ...props}) => <h2 className="text-lg font-bold text-[#00FF94] mt-4 mb-2" {...props} />,
                  h3: ({node, ...props}) => <h3 className="text-md font-semibold text-[#FFB800] mt-3 mb-2" {...props} />,
                  p: ({node, ...props}) => <p className="text-[#E4E4E7] mb-2 leading-relaxed" {...props} />,
                  ul: ({node, ...props}) => <ul className="list-disc list-inside mb-2 text-[#E4E4E7]" {...props} />,
                  ol: ({node, ...props}) => <ol className="list-decimal list-inside mb-2 text-[#E4E4E7]" {...props} />,
                  li: ({node, ...props}) => <li className="mb-1" {...props} />,
                  strong: ({node, ...props}) => <strong className="text-white font-semibold" {...props} />,
                  code: ({node, ...props}) => <code className="bg-[#0A0A0A] px-1.5 py-0.5 rounded text-[#00FF94]" {...props} />,
                }}
              >
                {message.content}
              </ReactMarkdown>
            ) : (
              <p>{message.content}</p>
            )}
          </div>
          
          {/* Related Topics */}
          {isAI && message.related_topics && message.related_topics.length > 0 && (
            <div className="mt-4 pt-3 border-t border-[#1F1F1F]">
              <p className="text-xs text-[#A1A1AA] mb-2">📚 Related Topics:</p>
              <div className="flex flex-wrap gap-2">
                {message.related_topics.map((topic, i) => (
                  <Badge
                    key={i}
                    className="bg-[#9D00FF]/20 text-[#9D00FF] cursor-pointer hover:bg-[#9D00FF]/30"
                    onClick={() => handleQuickQuestion(`Tell me about ${topic}`)}
                  >
                    {topic}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          
          {/* Follow-up Questions */}
          {isAI && message.follow_up_questions && message.follow_up_questions.length > 0 && (
            <div className="mt-3">
              <p className="text-xs text-[#A1A1AA] mb-2">💡 Keep Learning:</p>
              <div className="space-y-1">
                {message.follow_up_questions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => handleQuickQuestion(q)}
                    className="text-sm text-[#00FF94] hover:underline text-left flex items-center gap-1"
                  >
                    <ChevronRight size={14} />
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </motion.div>
    );
  };

  return (
    <div className="p-4 lg:p-8 space-y-6" data-testid="ai-teacher-page">
      {/* Header */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <GraduationCap className="text-[#9D00FF]" />
            AI Master Teacher
          </h1>
          <p className="text-[#A1A1AA] mt-1">Learn crypto, trading & blockchain with comprehensive 5W1H explanations</p>
        </div>
        
        <div className="flex items-center gap-3">
          <Select value={level} onValueChange={setLevel}>
            <SelectTrigger className="w-40 bg-[#121212] border-[#1F1F1F]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-[#121212] border-[#1F1F1F]">
              <SelectItem value="beginner">🌱 Beginner</SelectItem>
              <SelectItem value="intermediate">📊 Intermediate</SelectItem>
              <SelectItem value="advanced">🚀 Advanced</SelectItem>
              <SelectItem value="expert">🎓 Expert</SelectItem>
            </SelectContent>
          </Select>
          
          <Button variant="outline" className="border-[#1F1F1F]" onClick={clearHistory}>
            <Trash2 size={16} className="mr-2" />
            Clear
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-[#121212] border border-[#1F1F1F]">
          <TabsTrigger value="chat" className="data-[state=active]:bg-[#9D00FF]">
            <MessageCircle size={16} className="mr-2" />
            Learn
          </TabsTrigger>
          <TabsTrigger value="topics" className="data-[state=active]:bg-[#9D00FF]">
            <BookOpen size={16} className="mr-2" />
            Topics
          </TabsTrigger>
          <TabsTrigger value="glossary" className="data-[state=active]:bg-[#9D00FF]">
            <HelpCircle size={16} className="mr-2" />
            Glossary
          </TabsTrigger>
          <TabsTrigger value="quiz" className="data-[state=active]:bg-[#9D00FF]">
            <Trophy size={16} className="mr-2" />
            Quiz
          </TabsTrigger>
        </TabsList>

        {/* Chat Tab */}
        <TabsContent value="chat" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Chat Area */}
            <Card className="lg:col-span-3 bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="p-0">
                <div className="h-[60vh] overflow-y-auto p-4">
                  {messages.map((msg, i) => renderMessage(msg, i))}
                  {loading && (
                    <div className="flex justify-start mb-4">
                      <div className="bg-[#1A1A2E] rounded-2xl p-4">
                        <div className="flex items-center gap-2">
                          <Loader2 size={18} className="animate-spin text-[#9D00FF]" />
                          <span className="text-[#A1A1AA]">Teaching...</span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
                
                <div className="border-t border-[#1F1F1F] p-4">
                  <div className="flex gap-3">
                    <Input
                      ref={inputRef}
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Ask anything about crypto, trading, or blockchain..."
                      className="bg-[#121212] border-[#1F1F1F]"
                      disabled={loading}
                    />
                    <Button 
                      onClick={() => sendMessage(inputValue)}
                      disabled={loading || !inputValue.trim()}
                      className="bg-[#9D00FF] hover:bg-[#8800DD]"
                    >
                      {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Questions Sidebar */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Lightbulb className="text-[#FFB800]" size={18} />
                  Quick Questions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {topics?.quick_questions?.slice(0, 8).map((q, i) => (
                  <button
                    key={i}
                    onClick={() => handleQuickQuestion(q)}
                    className="w-full text-left text-sm text-[#A1A1AA] hover:text-white p-2 rounded hover:bg-[#1F1F1F] transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Topics Tab */}
        <TabsContent value="topics" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {topics?.topics?.map((category, i) => (
              <Card key={i} className="bg-[#0A0A0A] border-[#1F1F1F]">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg text-[#9D00FF]">{category.category}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {category.items.map((item, j) => (
                    <button
                      key={j}
                      onClick={() => handleQuickQuestion(item.title)}
                      className="w-full text-left p-3 rounded-lg bg-[#121212] hover:bg-[#1A1A2E] transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-white text-sm">{item.title}</span>
                        <Badge variant="outline" className={`text-xs ${
                          item.difficulty === 'beginner' ? 'border-[#00FF94] text-[#00FF94]' :
                          item.difficulty === 'intermediate' ? 'border-[#FFB800] text-[#FFB800]' :
                          item.difficulty === 'advanced' ? 'border-[#FF6B00] text-[#FF6B00]' :
                          'border-[#FF0055] text-[#FF0055]'
                        }`}>
                          {item.difficulty}
                        </Badge>
                      </div>
                    </button>
                  ))}
                  <Button 
                    variant="outline" 
                    className="w-full mt-2 border-[#9D00FF] text-[#9D00FF]"
                    onClick={() => loadQuiz(category.category.toLowerCase())}
                  >
                    <Trophy size={16} className="mr-2" />
                    Take Quiz
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Glossary Tab */}
        <TabsContent value="glossary" className="mt-4">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <BookOpen className="text-[#00FF94]" />
                  Crypto Glossary
                </CardTitle>
                <div className="relative w-64">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#A1A1AA]" />
                  <Input
                    placeholder="Search terms..."
                    value={glossarySearch}
                    onChange={(e) => {
                      setGlossarySearch(e.target.value);
                      loadGlossary(e.target.value);
                    }}
                    className="pl-10 bg-[#121212] border-[#1F1F1F]"
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[60vh] overflow-y-auto">
                {glossary.map((item, i) => (
                  <div 
                    key={i} 
                    className="p-4 bg-[#121212] rounded-lg cursor-pointer hover:bg-[#1A1A2E]"
                    onClick={() => handleQuickQuestion(`Explain ${item.term} in detail`)}
                  >
                    <div className="font-bold text-[#9D00FF] mb-1">{item.term}</div>
                    <div className="text-sm text-[#A1A1AA]">{item.definition}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Quiz Tab */}
        <TabsContent value="quiz" className="mt-4">
          {quiz ? (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Trophy className="text-[#FFB800]" />
                  {quiz.title}
                </CardTitle>
                <CardDescription>Test your knowledge - {quiz.questions.length} questions</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {quiz.questions.map((q, qIndex) => (
                  <div key={qIndex} className="p-4 bg-[#121212] rounded-lg">
                    <div className="font-medium text-white mb-3">
                      {qIndex + 1}. {q.question}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {q.options.map((option, oIndex) => {
                        const isSelected = quizAnswers[qIndex] === oIndex;
                        const isCorrect = q.correct === oIndex;
                        const showResult = quizSubmitted;
                        
                        return (
                          <button
                            key={oIndex}
                            onClick={() => !quizSubmitted && setQuizAnswers({...quizAnswers, [qIndex]: oIndex})}
                            disabled={quizSubmitted}
                            className={`p-3 rounded-lg text-left transition-colors flex items-center gap-2 ${
                              showResult
                                ? isCorrect
                                  ? 'bg-[#00FF94]/20 border-2 border-[#00FF94]'
                                  : isSelected
                                    ? 'bg-[#FF0055]/20 border-2 border-[#FF0055]'
                                    : 'bg-[#1F1F1F]'
                                : isSelected
                                  ? 'bg-[#9D00FF]/30 border-2 border-[#9D00FF]'
                                  : 'bg-[#1F1F1F] hover:bg-[#2F2F2F]'
                            }`}
                          >
                            {showResult && isCorrect && <CheckCircle size={16} className="text-[#00FF94]" />}
                            {showResult && isSelected && !isCorrect && <XCircle size={16} className="text-[#FF0055]" />}
                            <span className="text-sm">{option}</span>
                          </button>
                        );
                      })}
                    </div>
                    {quizSubmitted && (
                      <div className="mt-3 p-2 bg-[#1A1A2E] rounded text-sm text-[#A1A1AA]">
                        💡 {q.explanation}
                      </div>
                    )}
                  </div>
                ))}
                
                {!quizSubmitted ? (
                  <Button 
                    onClick={submitQuiz}
                    className="w-full bg-[#9D00FF] hover:bg-[#8800DD]"
                    disabled={Object.keys(quizAnswers).length !== quiz.questions.length}
                  >
                    Submit Quiz
                  </Button>
                ) : (
                  <div className="flex gap-4">
                    <Button 
                      onClick={() => loadQuiz(quiz.title.split(' ')[0].toLowerCase())}
                      variant="outline"
                      className="flex-1 border-[#9D00FF] text-[#9D00FF]"
                    >
                      Retake Quiz
                    </Button>
                    <Button 
                      onClick={() => setActiveTab('topics')}
                      className="flex-1 bg-[#00FF94] hover:bg-[#00DD7F] text-black"
                    >
                      Explore More Topics
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="p-12 text-center">
                <Trophy size={48} className="mx-auto mb-4 text-[#FFB800]" />
                <h3 className="text-xl font-bold text-white mb-2">Test Your Knowledge</h3>
                <p className="text-[#A1A1AA] mb-4">Select a topic from the Topics tab to take a quiz</p>
                <Button onClick={() => setActiveTab('topics')} className="bg-[#9D00FF]">
                  Browse Topics
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AITeacher;
