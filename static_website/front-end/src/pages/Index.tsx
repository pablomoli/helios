import Navigation from "@/components/Navigation";
import Hero from "@/components/Hero";
import Features from "@/components/Features";
import Journey from "@/components/Journey";
import Footer from "@/components/Footer";
import Chat from "@/components/Chat";

const Index = () => {
  return (
    <div className="min-h-screen">
      <Navigation />
      <main>
        <Hero />
        <Chat />
        <Features />
        <Journey />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
