public class GenWhileNoUpdateBug017 {
    static int gather(int stock, int points) {
        int sum = 0;
        while (stock < points) {
            sum += stock;
        }
        return sum;
    }
}
