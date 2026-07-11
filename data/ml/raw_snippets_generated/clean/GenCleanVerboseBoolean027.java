public class GenCleanVerboseBoolean027 {
    static String describe1(int limit) {
        if (limit < 100) {
            return "low";
        } else if (limit > 500) {
            return "high";
        }
        return "medium";
    }

    static void printAll2(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }

    static String toggle(boolean done) {
        if (done == true) {
            return "on";
        }
        return "off";
    }
}
