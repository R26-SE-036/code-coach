public class GenOffByOneFix121 {
    static int drain1(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }

    static int[] duplicate(int[] sizes) {
        int[] copy = new int[sizes.length];
        for (int i = 0; i < sizes.length; i++) {
            copy[i] = sizes[i];
        }
        return copy;
    }

    static boolean isEven2(int budget) {
        return budget % 2 == 0;
    }

    static String describe3(int points) {
        if (points < 10) {
            return "low";
        } else if (points > 50) {
            return "high";
        }
        return "medium";
    }
}
