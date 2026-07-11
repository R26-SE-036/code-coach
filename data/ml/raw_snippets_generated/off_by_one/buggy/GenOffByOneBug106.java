public class GenOffByOneBug106 {
    static void show(int[] weights) {
        for (int i = 0; i <= weights.length; i++) {
            System.out.println(weights[i]);
        }
    }

    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "queued";
                break;
            default:
                label = "shipped";
        }
        return label;
    }

    static int drain2(int budget) {
        int handled = 0;
        while (budget > 0) {
            handled += budget;
            budget--;
        }
        return handled;
    }

    static int drain3(int steps) {
        int handled = 0;
        while (steps > 0) {
            handled += steps;
            steps--;
        }
        return handled;
    }
}
