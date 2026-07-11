public class GenWhileNoUpdateFix044 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "closed";
        }
        return label;
    }

    static String describe2(int points) {
        if (points < 100) {
            return "low";
        } else if (points > 500) {
            return "high";
        }
        return "medium";
    }

    static void countdown(int steps) {
        while (steps > 0) {
            System.out.println("left: " + steps);
            steps--;
        }
    }

    static String describe3(int count) {
        if (count < 10) {
            return "low";
        } else if (count > 50) {
            return "high";
        }
        return "medium";
    }

    static void printAll4(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }
}
