import { useState } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { Card, CardContent } from "./ui/card";
import { Loader2 } from "lucide-react";

export default function LinkedInBotForm() {
  const [formData, setFormData] = useState({
    linkedinEmail: "",
    linkedinPassword: "",
    userEmail: "",
    emailPassword: "",
    keywords: "Software Engineer, Entry Level",
  });

  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResponse(null);

    try {
      const res = await fetch("http://localhost:5000/run-bot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setResponse({ error: "Something went wrong. Try again." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-blue-100 p-8 flex flex-col items-center">
      <Card className="w-full max-w-xl shadow-xl ">
        <CardContent className="space-y-6 p-6">
          <h1 className="text-2xl font-bold text-center">LinkedIn Job Bot</h1>
          <form onSubmit={handleSubmit} className="space-y-4 ">
            <Input
              type="email"
              name="linkedinEmail"
              placeholder="LinkedIn Email"
              value={formData.linkedinEmail}
              onChange={handleChange}
              required
            />
            <Input
              type="password"
              name="linkedinPassword"
              placeholder="LinkedIn Password"
              value={formData.linkedinPassword}
              onChange={handleChange}
              required
            />
            <Input
              type="email"
              name="userEmail"
              placeholder="Your Email (to receive links)"
              value={formData.userEmail}
              onChange={handleChange}
              required
            />
            <Input
              type="password"
              name="emailPassword"
              placeholder="App Password (Gmail)"
              value={formData.emailPassword}
              onChange={handleChange}
              required
            />
            <Textarea
              name="keywords"
              rows={3}
              placeholder="Job Keywords (comma separated)"
              value={formData.keywords}
              onChange={handleChange}
              required
            />
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="animate-spin mr-2" /> Running Bot...
                </>
              ) : (
                "Run Bot"
              )}
            </Button>
          </form>

          {response && (
            <div className="mt-4 text-center text-sm text-gray-700">
              {response.success ? (
                <div>✅ Bot finished successfully!</div>
              ) : (
                <div>❌ {response.error}</div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 