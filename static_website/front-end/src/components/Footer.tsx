import { Github, Linkedin, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";

const Footer = () => {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="border-t border-border bg-card/50 backdrop-blur">
      <div className="container px-4 py-12">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div className="space-y-4">
            <h3 className="text-2xl font-bold bg-clip-text text-transparent gradient-hero">
              Helios AI
            </h3>
            <p className="text-sm text-muted-foreground">
              Sun-tracking innovation built by college students for a sustainable future.
            </p>
          </div>
          
          {/* Links */}
          <div className="space-y-4">
            <h4 className="font-semibold">Project</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><a href="#features" className="hover:text-primary transition-smooth">Features</a></li>
              <li><a href="#journey" className="hover:text-primary transition-smooth">Our Journey</a></li>
              <li><a href="#demo" className="hover:text-primary transition-smooth">Live Demo</a></li>
            </ul>
          </div>
          
          {/* Tech Stack */}
          <div className="space-y-4">
            <h4 className="font-semibold">Tech Stack</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>Arduino</li>
              <li>Google Gemini AI</li>
              <li>React & TypeScript</li>
              <li>Tailwind CSS</li>
            </ul>
          </div>
          
          {/* Connect */}
          <div className="space-y-4">
            <h4 className="font-semibold">Connect</h4>
            <div className="flex gap-3">
              <Button variant="outline" size="icon" className="hover:border-primary">
                <Github className="w-4 h-4" />
              </Button>
              <Button variant="outline" size="icon" className="hover:border-primary">
                <Linkedin className="w-4 h-4" />
              </Button>
              <Button variant="outline" size="icon" className="hover:border-primary">
                <Mail className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
        
        <div className="pt-8 border-t border-border text-center text-sm text-muted-foreground">
          <p>© {currentYear} Helios AI. Crafted by college students for a sustainable tomorrow.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
