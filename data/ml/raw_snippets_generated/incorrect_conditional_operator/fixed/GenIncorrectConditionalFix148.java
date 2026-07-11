public class GenIncorrectConditionalFix148 {
    static void printAll1(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }

    static void announce(int quota) {
        if (quota == 5) {
            System.out.println("hit the target");
        }
    }
}
