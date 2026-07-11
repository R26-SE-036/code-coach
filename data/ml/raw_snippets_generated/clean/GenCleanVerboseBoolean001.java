public class GenCleanVerboseBoolean001 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static boolean isEven2(int attempts) {
        return attempts % 2 == 0;
    }

    static String toggle(boolean done) {
        if (done == true) {
            return "on";
        }
        return "off";
    }
}
