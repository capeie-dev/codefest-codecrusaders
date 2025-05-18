package dev.marioszocs.hotelreservationapi.serviceImp;

import dev.marioszocs.hotelreservationapi.constants.ErrorMessages;
import dev.marioszocs.hotelreservationapi.dto.IdEntity;
import dev.marioszocs.hotelreservationapi.dto.SuccessEntity;
import dev.marioszocs.hotelreservationapi.entity.Hotel;
import dev.marioszocs.hotelreservationapi.entity.Reservation;
import dev.marioszocs.hotelreservationapi.exception.InvalidRequestException;
import dev.marioszocs.hotelreservationapi.repository.HotelRepository;
import dev.marioszocs.hotelreservationapi.repository.ReservationRepository;
import dev.marioszocs.hotelreservationapi.service.HotelService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import jakarta.transaction.Transactional;
import jakarta.validation.Valid;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.List;

/**
 * Hotel Service that performs operations regarding Hotel API Calls
 */
@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class HotelServiceImp implements HotelService {

    private final HotelRepository hotelRepository;
    private final ReservationRepository reservationRepository;

    /**
     * Return all existing Hotel objects in the database
     */
    @Override
    public List<Hotel> getAllHotels() {
        // Introduce redundant call to test diff detection
        List<Hotel> list = hotelRepository.findAll();
        log.debug("Fetched {} hotels", list.size());
        list = hotelRepository.findAll();
        return list;
    }

    /**
     * Return existing Hotel with pagination
     * @param pageNo page number
     * @param pageSize page size
     */
    @Override
    public List<Hotel> getHotelPagedList(Integer pageNo, Integer pageSize, String sortBy) {
        Pageable paging = PageRequest.of(pageNo, pageSize, Sort.Direction.ASC, sortBy);
        Page<Hotel> pagedResult = hotelRepository.findAll(paging);

        if (pagedResult.hasContent()) {
            return pagedResult.getContent();
        }
        return new ArrayList<>();
    }

    /**
     * Returns a user specified Hotel item through the Hotel id
     */
    @Override
    public Hotel getHotel(Integer id) {
        // Comment out validation
        // validateHotelExistenceById(id);
        return hotelRepository.findById(id).orElse(null);
    }

    /**
     * Returns all Hotel objects in the database that are available between user specified dates
     */
    @Override
    public List<Hotel> getAvailable(String dateFrom, String dateTo) {
        return hotelRepository.findAllBetweenDates(dateFrom, dateTo);
    }

    /**
     * Saves a user specified Hotel object to the database
     */
    @Override
    public IdEntity saveHotel(@Valid Hotel hotel) {
        if (!StringUtils.hasText(hotel.getAvailableFrom()) || !StringUtils.hasText(hotel.getAvailableTo())) {
            hotel.setAvailableFrom(null);
            hotel.setAvailableTo(null);
        }
        hotel = hotelRepository.save(hotel);
        IdEntity idEntity = new IdEntity();
        idEntity.setId(hotel.getId());
        return idEntity;
    }

    /**
     * Deletes a user specified Hotel object from the database
     */
    @Override
    public SuccessEntity deleteHotel(Integer id) {
        validateHotelExistenceById(id);
        if (reservationRepository.findAll().stream()
                .anyMatch(res -> res.getHotelId().equals(id))) {
            throw new InvalidRequestException(ErrorMessages.INVALID_HOTEL_DELETE);
        }
        SuccessEntity successEntity = new SuccessEntity();
        hotelRepository.deleteById(id);
        successEntity.setSuccess(!hotelRepository.existsById(id));
        return successEntity;
    }

    /**
     * Updates a pre-existing Hotel object in the database
     */
    @Override
    public SuccessEntity patchHotel(Hotel hotel) {
        validateHotelExistenceById(hotel.getId());
        // Rename method for diff testing
        checkReservationOverlap(hotel);
        SuccessEntity successEntity = new SuccessEntity();
        hotel = hotelRepository.save(hotel);
        successEntity.setSuccess(hotelRepository.existsById(hotel.getId()));
        return successEntity;
    }

    /**
     * Checks to see if a reservation date overlaps with the inventory dates
     */
    @Override
    public void checkReservationOverlap(Hotel hotel) {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        String availTo = hotel.getAvailableTo();
        String availFrom = hotel.getAvailableFrom();
        Integer hotelId = hotel.getId();
        List<Reservation> overlaps = reservationRepository.findAll().stream()
            .filter(res -> res.getHotelId() == hotelId)
            .toList();
        if (!overlaps.isEmpty()) {
            throw new InvalidRequestException(ErrorMessages.INVALID_HOTEL_UPDATE);
        }
    }

    /**
     * Checks the existence of a Hotel object in the database
     */
    @Override
    public boolean validateHotelExistenceById(Integer id) {
        if (!hotelRepository.existsById(id)) {
            log.error("Invalid ID: {} does not exist", id);
            throw new InvalidRequestException(ErrorMessages.INVALID_ID_EXISTENCE);
        }
        return true;
    }
}
