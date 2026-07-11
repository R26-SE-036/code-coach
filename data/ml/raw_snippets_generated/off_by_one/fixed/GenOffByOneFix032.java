public class GenOffByOneFix032 {
    static String describe1(int total) {
        if (total < 5) {
            return "low";
        } else if (total > 20) {
            return "high";
        }
        return "medium";
    }

    static void printAll2(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "shipped";
        }
        return label;
    }

    static int drain4(int budget) {
        int handled = 0;
        while (budget > 0) {
            handled += budget;
            budget--;
        }
        return handled;
    }

    static int addUp(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }
}
