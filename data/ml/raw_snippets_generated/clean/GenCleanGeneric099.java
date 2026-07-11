public class GenCleanGeneric099 {
    static void printAll1(int[] prices) {
        for (int value : prices) {
            System.out.println(value);
        }
    }

    static String describe2(int budget) {
        if (budget < 10) {
            return "low";
        } else if (budget > 50) {
            return "high";
        }
        return "medium";
    }

    static void printAll3(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }
}
