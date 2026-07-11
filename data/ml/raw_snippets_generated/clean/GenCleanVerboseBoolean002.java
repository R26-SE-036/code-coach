public class GenCleanVerboseBoolean002 {
    static int largest1(int[] ages) {
        int best = ages[0];
        for (int i = 1; i < ages.length; i++) {
            if (ages[i] > best) {
                best = ages[i];
            }
        }
        return best;
    }

    static int drain2(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }

    static String toggle(boolean ready) {
        if (ready == true) {
            return "on";
        }
        return "off";
    }

    static boolean isEven3(int steps) {
        return steps % 2 == 0;
    }
}
