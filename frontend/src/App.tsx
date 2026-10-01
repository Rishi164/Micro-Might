import { Routes, Route } from "react-router-dom";
import Home from "@/pages/Home";
import About from "@/pages/About";
import Admin from "@/pages/Admin";
import Contact from "@/pages/Contact";
import Gyoc from "@/pages/Gyoc";
import Microgreens from "@/pages/Microgreens";
import Payment from "@/pages/Payment";
import WaysToEnjoy from "@/pages/WaysToEnjoy";
import Account from "@/pages/Account";
import Cart from "@/pages/Cart";
import Checkout from "@/pages/Checkout";
import Login from "@/pages/Login";
import ScrollToTop from "@/components/ScrollToTop";

// One <Route> per page in src/pages; BrowserRouter already wraps this in main.tsx.
export default function App() {
  return (
    <><ScrollToTop /><Routes>
      <Route path="/" element={<Home />} />
      <Route path="/microgreens" element={<Microgreens />} />
      <Route path="/gyoc" element={<Gyoc />} />
      <Route path="/ways-to-enjoy" element={<WaysToEnjoy />} />
      <Route path="/about" element={<About />} />
      <Route path="/contact" element={<Contact />} />
      <Route path="/payment" element={<Payment />} />
      <Route path="/admin" element={<Admin />} />
      <Route path="/cart" element={<Cart />} />
      <Route path="/checkout" element={<Checkout />} />
      <Route path="/login" element={<Login />} />
      <Route path="/account" element={<Account />} />
    </Routes></>
  );
}
