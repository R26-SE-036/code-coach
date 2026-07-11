public class GenCleanVerboseBoolean008 {
    static int largest1(int[] ages) {
        int best = ages[0];
        for (int i = 1; i < ages.length; i++) {
            if (ages[i] > best) {
                best = ages[i];
            }
        }
        return best;
    }

    static String toggle(boolean done) {
        if (done == true) {
            return "on";
        }
        return "off";
    }

    static String describe2(int stock) {
        if (stock < 5) {
            return "low";
        } else if (stock > 20) {
            return "high";
        }
        return "medium";
    }
}
