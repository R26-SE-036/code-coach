public class GenCleanGeneric015 {
    static void printAll1(int[] ages) {
        for (int value : ages) {
            System.out.println(value);
        }
    }

    static void printAll2(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
