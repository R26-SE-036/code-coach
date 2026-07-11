public class GenCleanWhileTrueBreak010 {
    static boolean isEven1(int steps) {
        return steps % 2 == 0;
    }

    static int spin(int budget) {
        int rounds = 0;
        while (true) {
            rounds++;
            if (rounds > budget) {
                break;
            }
        }
        return rounds;
    }

    static boolean isEven2(int budget) {
        return budget % 2 == 0;
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "draft";
                break;
            default:
                label = "expired";
        }
        return label;
    }
}
