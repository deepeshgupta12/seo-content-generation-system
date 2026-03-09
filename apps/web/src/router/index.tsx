import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "../components/AppLayout";
import { NotFoundPage } from "../pages/NotFoundPage";
import { ReviewWorkbenchPage } from "../pages/ReviewWorkbenchPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <ReviewWorkbenchPage />,
      },
    ],
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
]);
