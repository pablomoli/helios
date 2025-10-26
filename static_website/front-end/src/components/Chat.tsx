import { useState, FormEvent } from "react";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Send } from "lucide-react";

const Chat = () => {
    const [message, setMessage] = useState("");
    const [messages, setMessages] = useState<{ content: string; isUser: boolean }[]>([
        {
            content: "Hey there! We're college students who built Helios AI for a hackathon. I'm your voice-controlled assistant, powered by Google Gemini. Ask me about our solar-tracking robot or try a voice command to rotate the panel!",
            isUser: false
        }
    ]);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (!message.trim()) return;

        // Add user's message
        setMessages((prev) => [...prev, { content: message, isUser: true }]);
        const userMessage = message;
        setMessage("");

        // Add typing indicator
        setMessages((prev) => [...prev, { content: "...typing", isUser: false }]);

        try {
            const res = await fetch("/snowflake/complete", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMessage }),
            });

            const data = await res.json();

            // Remove typing indicator
            setMessages((prev) => prev.filter((msg) => msg.content !== "...typing"));

            // Add bot's response
            setMessages((prev) => [...prev, { content: data.botResponse, isUser: false }]);
        } catch (err) {
            // Remove typing indicator and show error
            setMessages((prev) => prev.filter((msg) => msg.content !== "...typing"));
            setMessages((prev) => [
                ...prev,
                { content: "Sorry, I cannot connect to the assistant right now.", isUser: false },
            ]);
            console.error(err);
        }
    };

    return (
        <div className="min-h-screen flex flex-col">
            <Navigation />

            <main className="flex-1 gradient-hero relative overflow-hidden">
                {/* Animated background pattern */}
                <div className="absolute inset-0 opacity-10">
                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(255,215,0,0.3),transparent_50%)] animate-pulse" />
                </div>

                <div className="container mx-auto px-4 py-12 relative z-10">
                    <div className="max-w-4xl mx-auto">
                        {/* Header */}
                        <div className="text-center mb-8">
                            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 backdrop-blur-sm border border-primary/20 mb-4">
                                <span className="relative flex h-2 w-2">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                                </span>
                                <span className="text-sm font-medium">AI Assistant Active</span>
                            </div>
                            <h1 className="text-4xl md:text-5xl font-bold mb-3 bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent">
                                Helios AI Chatbot
                            </h1>
                            <p className="text-muted-foreground">Powered by Google Gemini</p>
                        </div>

                        {/* Chat Container */}
                        <div className="bg-background/95 backdrop-blur-xl rounded-3xl shadow-glow border border-primary/20 overflow-hidden">
                            {/* Messages */}
                            <div className="h-[500px] overflow-y-auto p-6 space-y-4" id="chat-window">
                                {messages.map((msg, idx) => (
                                    <div
                                        key={idx}
                                        className={`flex ${msg.isUser ? "justify-end" : "justify-start"} animate-fade-in`}
                                    >
                                        <div
                                            className={`max-w-[80%] p-4 rounded-2xl shadow-soft transition-smooth ${msg.isUser
                                                ? "bg-gradient-to-br from-primary to-primary/80 text-primary-foreground ml-12"
                                                : "bg-muted/50 backdrop-blur-sm border border-border mr-12"
                                                }`}
                                        >
                                            {msg.content}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Input Form */}
                            <div className="p-6 border-t border-border bg-muted/30 backdrop-blur-sm">
                                <form onSubmit={handleSubmit} className="flex gap-3">
                                    <input
                                        type="text"
                                        value={message}
                                        onChange={(e) => setMessage(e.target.value)}
                                        placeholder="Try 'Rotate panel left' or ask about our project..."
                                        className="flex-1 px-4 py-3 bg-background border border-input rounded-xl focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-smooth"
                                    />
                                    <Button type="submit" size="lg" className="px-6 shadow-glow">
                                        <Send className="h-4 w-4" />
                                    </Button>
                                </form>
                                <p className="text-xs text-muted-foreground text-center mt-3">
                                    Built by students, powered by Google Gemini
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            <Footer />
        </div>
    );
};

export default Chat;
