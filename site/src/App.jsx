import "./styles/tokens.css";
import "./styles/reveal.css";
import Nav from "./components/Nav";
import Hero from "./components/Hero";
import Sellers from "./components/Sellers";
import Dashboard from "./components/Dashboard";
import Deletion from "./components/Deletion";
import Tiers from "./components/Tiers";
import Scoring from "./components/Scoring";
import Developers from "./components/Developers";
import useReveal from "./hooks/useReveal";

const REPO = "#";
const VIDEO = "#";

export default function App() {
  useReveal();
  return (
    <>
      <Nav repoUrl={REPO} />
      <Hero repoUrl={REPO} videoUrl={VIDEO} />
      <Sellers />
      <Dashboard repoUrl={REPO} videoUrl={VIDEO} />
      <Deletion />
      <Tiers />
      <Scoring videoUrl={VIDEO} />
      <Developers />
    </>
  );
}
