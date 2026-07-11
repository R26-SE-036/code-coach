public class GenArrayIndexBug151 {
    static void printAll1(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }

    static String describe2(int count) {
        if (count < 10) {
            return "low";
        } else if (count > 50) {
            return "high";
        }
        return "medium";
    }

    static void showLast(int[] sizes) {
        System.out.println(sizes[sizes.length]);
    }
}
