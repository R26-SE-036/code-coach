public class GenCleanGeneric059 {
    static String describe1(int points) {
        if (points < 100) {
            return "low";
        } else if (points > 500) {
            return "high";
        }
        return "medium";
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void printAll3(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }
}
