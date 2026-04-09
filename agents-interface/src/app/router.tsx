import { createBrowserRouter } from "react-router-dom"

// imports das landing pages
import AiCrm from "../pages/ai-crm/ai-crm"
import Trainify from "../pages/trainify-ai/trainify"
import ContractAi from "../pages/contract-ai/contract-ai"
import CliniflowAi from "../pages/cliniflow/cliniflow"
import Home from "../pages/home/home"


export const router = createBrowserRouter([
  {
    path: "/",
    element: <Home />,
  },
  {
    path: "/ai-crm",
    element: <AiCrm />,
  },
  {
    path: "/trainify",
    element: <Trainify/>,
  },
  {
    path: "/contract-ai",
    element: <ContractAi/>,
  },
  {
    path: "/cliniflow-ai",
    element: <CliniflowAi/>,
  },
])