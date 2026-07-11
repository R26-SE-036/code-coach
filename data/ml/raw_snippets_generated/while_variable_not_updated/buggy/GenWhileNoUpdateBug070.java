public class GenWhileNoUpdateBug070 {
    static void printAll1(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }

    static void printAll2(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }

    static int gather(int budget, int total) {
        int sum = 0;
        while (budget < total) {
            sum += budget;
        }
        return sum;
    }
}
