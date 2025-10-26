import { Button } from "@/components/ui/button";
import { Sun, Mic, Zap } from "lucide-react";
import heroRobot from "@/assets/hero-robot.jpg";

const Hero = () => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-muted">
        <div className="absolute inset-0 opacity-20">
          <img 
            src={heroRobot} 
            alt="" 
            className="w-full h-full object-cover"
          />
        </div>
      </div>
      
      {/* Animated glow effects */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      
      <div className="container relative z-10 px-4 py-20">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-card border-2 border-primary/20 shadow-soft">
            <Zap className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium">Hackathon Innovation 2025</span>
          </div>
          
          {/* Main heading */}
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary via-accent to-secondary animate-in fade-in slide-in-from-bottom-4 duration-1000">
            Helios AI
          </h1>
          
          <p className="text-2xl md:text-3xl text-muted-foreground font-semibold animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-200">
            Sun-Chasing Innovation
          </p>
          
          <p className="text-lg md:text-xl text-foreground/80 max-w-3xl mx-auto leading-relaxed animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-300">
            A solar-tracking robot built by college students that maximizes energy efficiency using Arduino, 
            light sensors, and voice control powered by Google Gemini AI.
          </p>
          
          {/* Feature highlights */}
          <div className="flex flex-wrap justify-center gap-6 pt-4 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-500">
            <div className="flex items-center gap-2 text-foreground">
              <Sun className="w-5 h-5 text-primary" />
              <span className="font-medium">Solar Tracking</span>
            </div>
            <div className="flex items-center gap-2 text-foreground">
              <Mic className="w-5 h-5 text-secondary" />
              <span className="font-medium">Voice Control</span>
            </div>
            <div className="flex items-center gap-2 text-foreground">
              <Zap className="w-5 h-5 text-accent" />
              <span className="font-medium">Arduino Powered</span>
            </div>
          </div>
          
          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-8 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-700">
            <Button variant="hero" size="lg" className="text-lg px-8">
              <Mic className="w-5 h-5" />
              Try Voice Control
            </Button>
            <Button variant="outline" size="lg" className="text-lg px-8">
              <Sun className="w-5 h-5" />
              Learn More
            </Button>
          </div>
        </div>
      </div>
      
      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
        <div className="w-6 h-10 border-2 border-primary rounded-full flex items-start justify-center p-2">
          <div className="w-1 h-3 bg-primary rounded-full" />
        </div>
      </div>
    </section>
  );
};

export default Hero;
