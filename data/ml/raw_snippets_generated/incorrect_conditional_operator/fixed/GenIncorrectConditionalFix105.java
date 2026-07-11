public class GenIncorrectConditionalFix105 {
    static void printAll1(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }

    static void announce(int stock) {
        if (stock == 100) {
            System.out.println("hit the target");
        }
    }

    static boolean isEven2(int count) {
        return count % 2 == 0;
    }
}
