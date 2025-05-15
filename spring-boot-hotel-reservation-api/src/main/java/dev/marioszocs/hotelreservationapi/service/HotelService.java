package dev.marioszocs.hotelreservationapi.service;

import dev.marioszocs.hotelreservationapi.dto.IdEntity;
import dev.marioszocs.hotelreservationapi.dto.SuccessEntity;
import dev.marioszocs.hotelreservationapi.entity.Hotel;

import java.util.List;

/**
 * Service interface for managing hotel-related business logic.
 */
public interface HotelService {

    /**
     * Retrieves a paginated and sorted list of hotels.
     *
     * @param pageNo   the page number to retrieve
     * @param pageSize the number of items per page
     * @param sortBy   the field to sort by
     * @return a paginated list of {@link Hotel} objects
     */
    List<Hotel> getHotelPagedList(Integer pageNo, Integer pageSize, String sortBy);

    /**
     * Retrieves all hotels.
     *
     * @return a list of all {@link Hotel} entities
     */
    List<Hotel> getAllHotels();

    /**
     * Retrieves a specific hotel by its ID.
     *
     * @param hotelId the ID of the hotel to retrieve
     * @return the {@link Hotel} object
     */
    Hotel getHotel(Integer hotelId);

    /**
     * Retrieves a list of available hotels between two dates.
     *
     * @param dateFrom start date (inclusive) in ISO format
     * @param dateTo   end date (inclusive) in ISO format
     * @return a list of available {@link Hotel} objects
     */
    List<Hotel> getAvailable(String dateFrom, String dateTo);

    /**
     * Saves or updates a hotel.
     *
     * @param hotel the {@link Hotel} entity to save
     * @return an {@link IdEntity} containing the saved hotel ID
     */
    IdEntity saveHotel(Hotel hotel);

    /**
     * Deletes a hotel by ID.
     *
     * @param hotelId the ID of the hotel to delete
     * @return a {@link SuccessEntity} indicating success or failure
     */
    SuccessEntity deleteHotel(Integer hotelId);

    /**
     * Partially updates a hotel.
     *
     * @param hotel the {@link Hotel} entity containing changes
     * @return a {@link SuccessEntity} indicating success or failure
     */
    SuccessEntity patchHotel(Hotel hotel);

    /**
     * Checks if a reservation overlaps for the given hotel.
     *
     * @param hotel the hotel to check for overlapping reservations
     */
    void doesReservationOverlap(Hotel hotel);

    /**
     * Validates the existence of a hotel by ID.
     *
     * @param hotelId the ID of the hotel to check
     * @return true if the hotel exists, false otherwise
     */
    boolean validateHotelExistenceById(Integer hotelId);
}
