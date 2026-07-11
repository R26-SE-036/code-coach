public class GenCleanVerboseBoolean028 {
    static int largest1(int[] marks) {
        int best = marks[0];
        for (int i = 1; i < marks.length; i++) {
            if (marks[i] > best) {
                best = marks[i];
            }
        }
        return best;
    }

    static String toggle(boolean armed) {
        if (armed == true) {
            return "on";
        }
        return "off";
    }
}
