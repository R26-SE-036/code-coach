public class GenOffByOneBug134 {
    static void printAll1(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }

    static int sum2(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
    }

    static void show(int[] ages) {
        for (int i = 0; i <= ages.length; i++) {
            System.out.println(ages[i]);
        }
    }
}
